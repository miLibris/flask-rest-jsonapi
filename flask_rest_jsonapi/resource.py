# -*- coding: utf-8 -*-

import inspect
from six import with_metaclass
import json

from werkzeug.wrappers import Response
from flask import request, url_for, make_response
from flask.views import MethodViewType, MethodView
from marshmallow_jsonapi.exceptions import IncorrectTypeError

from flask_rest_jsonapi.errors import ErrorFormatter
from flask_rest_jsonapi.querystring import QueryStringManager as QSManager
from flask_rest_jsonapi.pagination import add_pagination_links
from flask_rest_jsonapi.exceptions import EntityNotFound
from flask_rest_jsonapi.decorators import disable_method, check_headers, check_requirements, add_headers


class ResourceMeta(MethodViewType):

    def __init__(cls, name, bases, nmspc):
        super(ResourceMeta, cls).__init__(name, bases, nmspc)
        meta = nmspc.get('Meta')

        if meta is not None:
            data_layer = getattr(meta, 'data_layer', None)

            if data_layer is not None:
                if not isinstance(data_layer, dict):
                    raise Exception("You must provide data layer informations as dictionary")
                if data_layer.get('cls') is None:
                    raise Exception("You must provide a data layer class")
                else:
                    if 'BaseDataLayer' not in [cls_.__name__ for cls_ in inspect.getmro(data_layer['cls'])]:
                        raise Exception("You must provide a data layer class inherited from BaseDataLayer")

                data_layer_kwargs = {}
                data_layer_kwargs['resource_cls'] = cls
                data_layer_kwargs.update(data_layer.get('kwargs', {}))
                cls.data_layer = type('DataLayer', (data_layer['cls'], ), {})(**data_layer_kwargs)
                cls.data_layer.configure(data_layer)

            not_allowed_methods = getattr(meta, 'not_allowed_methods', [])
            for not_allowed_method in not_allowed_methods:
                if hasattr(cls, not_allowed_method.lower()):
                    setattr(cls, not_allowed_method.lower(), disable_method(getattr(cls, not_allowed_method.lower())))


class ResourceListMeta(ResourceMeta):

    def __init__(cls, name, bases, nmspc):
        super(ResourceListMeta, cls).__init__(name, bases, nmspc)
        meta = nmspc.get('Meta')

        if meta is not None:
            get_decorators = getattr(meta, 'get_decorators', [])
            post_decorators = getattr(meta, 'post_decorators', [])

            for get_decorator in get_decorators:
                cls.get = get_decorator(cls.get)

            for post_decorator in post_decorators:
                cls.post = post_decorator(cls.post)


class ResourceDetailMeta(ResourceMeta):

    def __init__(cls, name, bases, nmspc):
        super(ResourceDetailMeta, cls).__init__(name, bases, nmspc)
        meta = nmspc.get('Meta')

        if meta is not None:
            get_decorators = getattr(meta, 'get_decorators', [])
            patch_decorators = getattr(meta, 'patch_decorators', [])
            delete_decorators = getattr(meta, 'delete_decorators', [])

            for get_decorator in get_decorators:
                cls.get = get_decorator(cls.get)

            for patch_decorator in patch_decorators:
                cls.patch = patch_decorator(cls.patch)

            for delete_decorator in delete_decorators:
                cls.delete = delete_decorator(cls.delete)


class Resource(MethodView):
    """Base Resource class to serialize the response of the resource internal methods (get, post, patch, delete).
    According to jsonapi reference, returns a json string and the right status code.
    """
    decorators = (check_headers, add_headers)

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)
        if meth is None and request.method == 'HEAD':
            meth = getattr(self, 'get', None)
        assert meth is not None, 'Unimplemented method %r' % request.method

        resp = meth(*args, **kwargs)

        if isinstance(resp, Response):
            return resp

        if not isinstance(resp, tuple):
            return make_response(json.dumps(resp))

        try:
            data, status_code, headers = resp
        except ValueError:
            pass

        try:
            data, status_code = resp
            headers = {}
        except ValueError:
            pass

        return make_response(json.dumps(data), status_code, headers)


class ResourceList(with_metaclass(ResourceListMeta, Resource)):

    @check_requirements
    def get(self, *args, **kwargs):
        """Retrieve a collection of items
        """
        qs = QSManager(request.args)

        try:
            item_count, items = self.data_layer.get_items(qs, **kwargs)
        except EntityNotFound as e:
            return ErrorFormatter.format_error([e.message]), e.status_code

        schema_kwargs = self.schema.get('get_kwargs', {})
        if qs.fields.get(self.resource_type):
            if schema_kwargs.get('only'):
                schema_kwargs['only'] = tuple(set(schema_kwargs['only']) &
                                              set(self.schema['cls']._declared_fields.keys()) &
                                              set(qs.fields[self.resource_type]))
            else:
                schema_kwargs['only'] = tuple(set(self.schema['cls']._declared_fields.keys()) &
                                              set(qs.fields[self.resource_type]))
        if schema_kwargs.get('only') and 'id' not in schema_kwargs['only']:
            schema_kwargs['only'] += ('id',)
        schema_kwargs.pop('many', None)
        schema = self.schema['cls'](many=True, **schema_kwargs)

        result = schema.dump(items)

        endpoint_kwargs = request.view_args if self.endpoint.get('include_view_args') is True else {}
        add_pagination_links(result.data,
                             item_count,
                             qs,
                             url_for(self.endpoint.get('full_endpoint'), **endpoint_kwargs))

        return result.data

    @check_requirements
    def post(self, *args, **kwargs):
        """Create an item
        """
        json_data = request.get_json()

        schema = self.schema['cls'](**self.schema.get('post_kwargs', {}))
        try:
            data, errors = schema.load(json_data)
        except IncorrectTypeError as err:
            return err.messages, 409

        if errors:
            return errors, 422

        try:
            item = self.data_layer.create_and_save_item(data, **kwargs)
        except EntityNotFound as e:
            return ErrorFormatter.format_error([e.message]), e.status_code

        return schema.dump(item).data, 201


class ResourceDetail(with_metaclass(ResourceDetailMeta, Resource)):

    @check_requirements
    def get(self, *args, **kwargs):
        """Get item details
        """
        try:
            item = self.data_layer.get_item(**kwargs)
        except EntityNotFound as e:
            return ErrorFormatter.format_error([e.message]), e.status_code

        qs = QSManager(request.args)

        schema_kwargs = self.schema.get('get_kwargs', {})
        if qs.fields.get(self.resource_type):
            if schema_kwargs.get('only'):
                schema_kwargs['only'] = tuple(set(schema_kwargs['only']) &
                                              set(self.schema['cls']._declared_fields.keys()) &
                                              set(qs.fields[self.resource_type]))
            else:
                schema_kwargs['only'] = tuple(set(self.schema['cls']._declared_fields.keys()) &
                                              set(qs.fields[self.resource_type]))
        if schema_kwargs.get('only') and 'id' not in schema_kwargs['only']:
            schema_kwargs['only'] += ('id',)
        schema = self.schema['cls'](**schema_kwargs)

        result = schema.dump(item)

        return result.data

    @check_requirements
    def patch(self, *args, **kwargs):
        """Update an item
        """
        json_data = request.get_json()

        try:
            if json_data['data']['id'] is None:
                raise KeyError
        except KeyError:
            return ErrorFormatter.format_error(["You must provide id of the entity"]), 422

        schema_kwargs = self.schema.get('patch_kwargs', {})
        schema_kwargs.pop('partial', None)
        schema = self.schema['cls'](partial=True, **schema_kwargs)
        try:
            data, errors = schema.load(json_data)
        except IncorrectTypeError as err:
            return err.messages, 409

        if errors:
            return errors, 422

        try:
            item = self.data_layer.get_item(**kwargs)
        except EntityNotFound as e:
            return ErrorFormatter.format_error([e.message]), e.status_code

        self.data_layer.update_and_save_item(item, data, **kwargs)

        result = schema.dump(item)

        return result.data

    @check_requirements
    def delete(self, *args, **kwargs):
        """Delete an item
        """
        try:
            item = self.data_layer.get_item(**kwargs)
        except EntityNotFound as e:
            return ErrorFormatter.format_error([e.message]), e.status_code

        self.data_layer.delete_item(item, **kwargs)

        return '', 204
