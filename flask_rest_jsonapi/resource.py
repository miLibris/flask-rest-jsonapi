# -*- coding: utf-8 -*-

import inspect
from six import with_metaclass
import json
from copy import copy

from werkzeug.wrappers import Response
from flask import request, url_for, make_response
from flask.views import MethodViewType, MethodView
from marshmallow_jsonapi.exceptions import IncorrectTypeError
from marshmallow import ValidationError

from flask_rest_jsonapi.errors import jsonapi_errors_serializer
from flask_rest_jsonapi.querystring import QueryStringManager as QSManager
from flask_rest_jsonapi.pagination import add_pagination_links
from flask_rest_jsonapi.exceptions import ObjectNotFound, RelationNotFound, InvalidField, InvalidInclude, InvalidType, \
    BadRequest
from flask_rest_jsonapi.decorators import disable_method, check_headers, check_requirements, add_headers
from flask_rest_jsonapi.schema import compute_schema


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

            disabled_methods = getattr(meta, 'disabled_methods', [])
            for method in disabled_methods:
                if hasattr(cls, method.lower()):
                    setattr(cls, method.lower(), disable_method(getattr(cls, method.lower())))


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


class ResourceRelationshipMeta(ResourceMeta):

    def __init__(cls, name, bases, nmspc):
        super(ResourceRelationshipMeta, cls).__init__(name, bases, nmspc)
        meta = nmspc.get('Meta')

        if meta is not None:
            get_decorators = getattr(meta, 'get_decorators', [])
            post_decorators = getattr(meta, 'post_decorators', [])
            patch_decorators = getattr(meta, 'patch_decorators', [])
            delete_decorators = getattr(meta, 'delete_decorators', [])

            for get_decorator in get_decorators:
                cls.get = get_decorator(cls.get)

            for post_decorator in post_decorators:
                cls.post = post_decorator(cls.post)

            for patch_decorator in patch_decorators:
                cls.patch = patch_decorator(cls.patch)

            for delete_decorator in delete_decorators:
                cls.delete = delete_decorator(cls.delete)


class Resource(MethodView):

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

        item_count, items = self.data_layer.get_items(qs, **kwargs)

        schema_kwargs = self.schema.get('get_kwargs', {})
        schema_kwargs.update({'many': True})
        try:
            schema = compute_schema(self.schema['cls'], schema_kwargs, qs, None)
        except InvalidField as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        result = schema.dump(items)

        endpoint_kwargs = request.view_args if self.endpoint.get('include_view_kwargs') is True else {}
        add_pagination_links(result.data,
                             item_count,
                             qs,
                             url_for(self.endpoint.get('name'), **endpoint_kwargs))

        return result.data

    @check_requirements
    def post(self, *args, **kwargs):
        """Create an item
        """
        json_data = request.get_json()

        schema = self.schema['cls'](**self.schema.get('post_kwargs', {}))
        try:
            data, errors = schema.load(json_data)
        except IncorrectTypeError as e:
            errors = e.messages
            for error in errors['errors']:
                error['status'] = '409'
                error['title'] = "Incorrect type"
            return errors, 409
        except ValidationError as e:
            errors = e.messages
            for message in errors['errors']:
                message['status'] = '422'
                message['title'] = "Validation error"
            return errors, 422

        if errors:
            for error in errors['errors']:
                error['status'] = "422"
                error['title'] = "Validation error"
            return errors, 422

        item = self.data_layer.create_and_save_item(data, **kwargs)

        return schema.dump(item).data, 201


class ResourceDetail(with_metaclass(ResourceDetailMeta, Resource)):

    @check_requirements
    def get(self, *args, **kwargs):
        """Get item details
        """
        try:
            item = self.data_layer.get_item(**kwargs)
        except ObjectNotFound as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        qs = QSManager(request.args)
        try:
            schema = compute_schema(self.schema['cls'], self.schema.get('get_kwargs', {}), qs, qs.include)
        except (InvalidField, InvalidInclude) as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        result = schema.dump(item)
        return result.data

    @check_requirements
    def patch(self, *args, **kwargs):
        """Update an item
        """
        json_data = request.get_json()

        schema_kwargs = self.schema.get('patch_kwargs', {})
        schema_kwargs.pop('partial', None)
        schema = self.schema['cls'](partial=True, **schema_kwargs)
        try:
            data, errors = schema.load(json_data)
        except IncorrectTypeError as e:
            errors = e.messages
            for error in errors['errors']:
                error['status'] = '409'
                error['title'] = "Incorrect type"
            return errors, 409
        except ValidationError as e:
            errors = e.messages
            for message in errors['errors']:
                message['status'] = '422'
                message['title'] = "Validation error"
            return errors, 422

        if errors:
            for error in errors['errors']:
                error['status'] = "422"
                error['title'] = "Validation error"
            return errors, 422

        try:
            if 'id' not in json_data['data']:
                raise BadRequest('/data/id', 'Missing id in "data" node')
            if json_data['data']['id'] != kwargs[self.data_layer.url_param_name]:
                raise BadRequest('/data/id', 'Value of id does not match the resource identifier in url')
        except BadRequest as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        try:
            item = self.data_layer.get_item(**kwargs)
        except ObjectNotFound as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        self.data_layer.update_and_save_item(item, data, **kwargs)

        result = schema.dump(item)

        return result.data

    @check_requirements
    def delete(self, *args, **kwargs):
        """Delete an item
        """
        try:
            item = self.data_layer.get_item(**kwargs)
        except ObjectNotFound as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        self.data_layer.delete_item(item, **kwargs)

        return '', 204


class Relationship(with_metaclass(ResourceRelationshipMeta, Resource)):

    @check_requirements
    def get(self, *args, **kwargs):
        """Get a relationship details
        """
        try:
            item, data = self.data_layer.get_relationship(self.related_resource_type, self.related_id_field, **kwargs)
        except (RelationNotFound, ObjectNotFound) as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        related_endpoint_kwargs = kwargs
        if hasattr(self, 'endpoint_kwargs'):
            for key, value in copy(self.endpoint_kwargs).items():
                tmp_endpoint_kwargs_value = item
                for attr in value.split('.'):
                    tmp_endpoint_kwargs_value = getattr(tmp_endpoint_kwargs_value, attr)
                endpoint_kwargs_value = tmp_endpoint_kwargs_value
                self.endpoint_kwargs[key] = endpoint_kwargs_value
            related_endpoint_kwargs = self.endpoint_kwargs

        result = {'links': {'self': url_for(self.endpoint, **kwargs),
                            'related': url_for(self.related_endpoint, **related_endpoint_kwargs)},
                  'data': data}

        qs = QSManager(request.args)
        if qs.include:
            try:
                schema = compute_schema(self.schema, dict(), qs, qs.include)
            except (InvalidField, InvalidInclude) as e:
                return jsonapi_errors_serializer([e.to_dict()]), e.status

            serialized_item = schema.dump(item)
            result['included'] = serialized_item.data['included']

        return result

    @check_requirements
    def post(self, *args, **kwargs):
        """Add / create relationship(s)
        """
        json_data = request.get_json()

        try:
            if 'data' not in json_data:
                raise BadRequest('/data', 'You must provide data with a "data" route node')
            if not isinstance(json_data.get('data'), list):
                raise BadRequest('/data', 'You must provide data as list')
            for item in json_data['data']:
                if 'type' not in item:
                    raise BadRequest('/data/type', 'Missing type in "data" node')
                if 'id' not in item:
                    raise BadRequest('/data/id', 'Missing id in "data" node')
                if item['type'] != self.resource_type:
                    raise InvalidType('/data/type', 'The type provided does not match the resource type')
        except (BadRequest, InvalidType) as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        try:
            self.data_layer.add_relationship(json_data, self.related_id_field, **kwargs)
        except (RelationNotFound, ObjectNotFound) as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        return ''

    @check_requirements
    def patch(self, *args, **kwargs):
        """Update a relationship
        """
        json_data = request.get_json()

        try:
            if 'data' not in json_data:
                raise BadRequest('/data', 'You must provide data with a "data" route node')
            if isinstance(json_data['data'], dict):
                if 'type' not in json_data['data']:
                    raise BadRequest('/data/type', 'Missing type in "data" node')
                if 'id' not in json_data['data']:
                    raise BadRequest('/data/id', 'Missing id in "data" node')
                if json_data['data']['type'] != self.resource_type:
                    raise InvalidType('/data/type', 'The type field does not match the resource type')
            if isinstance(json_data['data'], list):
                for item in json_data['data']:
                    if 'type' not in item:
                        raise BadRequest('/data/type', 'Missing type in "data" node')
                    if 'id' not in item:
                        raise BadRequest('/data/id', 'Missing id in "data" node')
                    if item['type'] != self.resource_type:
                        raise InvalidType('/data/type', 'The type provided does not match the resource type')
        except (BadRequest, InvalidType) as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        try:
            self.data_layer.update_relationship(json_data, self.related_id_field, **kwargs)
        except (RelationNotFound, ObjectNotFound) as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        return ''

    @check_requirements
    def delete(self, *args, **kwargs):
        """Delete relationship(s)
        """
        json_data = request.get_json()

        try:
            if 'data' not in json_data:
                raise BadRequest('/data', 'You must provide data with a "data" route node')
            if not isinstance(json_data.get('data'), list):
                raise BadRequest('/data', 'You must provide data as list')
            for item in json_data['data']:
                if 'type' not in item:
                    raise BadRequest('/data/type', 'Missing type in "data" node')
                if 'id' not in item:
                    raise BadRequest('/data/id', 'Missing id in "data" node')
                if item['type'] != self.resource_type:
                    raise InvalidType('/data/type', 'The type provided does not match the resource type')
        except (BadRequest, InvalidType) as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        try:
            self.data_layer.remove_relationship(json_data, self.related_id_field, **kwargs)
        except RelationNotFound as e:
            return jsonapi_errors_serializer([e.to_dict()]), e.status

        return ''
