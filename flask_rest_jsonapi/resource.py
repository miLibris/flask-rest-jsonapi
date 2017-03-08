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

from flask_rest_jsonapi.errors import jsonapi_errors
from flask_rest_jsonapi.querystring import QueryStringManager as QSManager
from flask_rest_jsonapi.pagination import add_pagination_links
from flask_rest_jsonapi.exceptions import InvalidType, BadRequest, JsonApiException, RelationNotFound
from flask_rest_jsonapi.decorators import not_allowed_method, check_headers, check_method_requirements, add_headers
from flask_rest_jsonapi.schema import compute_schema, get_relationships
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.data_layers.alchemy import SqlalchemyDataLayer


class ResourceMeta(MethodViewType):

    def __init__(cls, name, bases, nmspc):
        super(ResourceMeta, cls).__init__(name, bases, nmspc)
        meta = nmspc.get('Meta')

        # compute data_layer
        data_layer = None

        alternative_data_layer_cls = getattr(meta, 'data_layer', None)
        if alternative_data_layer_cls is not None and BaseDataLayer not in inspect.getmro(alternative_data_layer_cls):
            raise Exception("You must provide a data layer class inherited from BaseDataLayer in {} resource"
                            .format(name))

        if nmspc.get('data_layer_kwargs') is not None:
            if not isinstance(nmspc['data_layer_kwargs'], dict):
                raise Exception("You must provide data_layer_kwargs as dictionary in {} resource".format(name))
            else:
                data_layer_cls = getattr(meta, 'data_layer', SqlalchemyDataLayer)
                data_layer_kwargs = nmspc.get('data_layer_kwargs', dict())
                data_layer = data_layer_cls(**data_layer_kwargs)
                data_layer.configure(meta)

        if data_layer is not None:
            data_layer.resource = cls
            cls.data_layer = data_layer

        # disable access to methods according to meta options
        if meta is not None:
            not_allowed_methods = getattr(meta, 'not_allowed_methods', [])
            for method in not_allowed_methods:
                if hasattr(cls, method.lower()):
                    setattr(cls, method.lower(), not_allowed_method(getattr(cls, method.lower())))

        # set meta information as opts of the resource class
        cls.opts = meta


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
        assert meth is not None, 'Unimplemented method {}'.format(request.method)

        try:
            resp = meth(*args, **kwargs)
        except JsonApiException as e:
            return make_response(json.dumps(jsonapi_errors([e.to_dict()])),
                                 e.status,
                                 {'Content-Type': 'application/vnd.api+json'})
#        except Exception as e:
#            exc = JsonApiException('', str(e))
#            return make_response(json.dumps(jsonapi_errors([exc.to_dict()])),
#                                 exc.status,
#                                 {'Content-Type': 'application/vnd.api+json'})

        if isinstance(resp, Response):
            return resp

        if not isinstance(resp, tuple):
            if isinstance(resp, dict):
                resp.update({'jsonapi': {'version': '1.0'}})
            return make_response(json.dumps(resp), 200, {'Content-Type': 'application/vnd.api+json'})

        try:
            data, status_code, headers = resp
        except ValueError:
            pass

        try:
            data, status_code = resp
            headers = {'Content-Type': 'application/vnd.api+json'}
        except ValueError:
            pass

        if isinstance(data, dict):
            data.update({'jsonapi': {'version': '1.0'}})

        return make_response(json.dumps(data), status_code, headers)


class ResourceList(with_metaclass(ResourceListMeta, Resource)):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Retrieve a collection of objects
        """
        qs = QSManager(request.args, self.schema)

        object_count, objects = self.data_layer.get_collection(qs, **kwargs)

        schema_kwargs = getattr(self.opts, 'schema_get_kwargs', dict())
        schema_kwargs.update({'many': True})

        schema = compute_schema(self.schema,
                                schema_kwargs,
                                qs,
                                qs.include)

        result = schema.dump(objects)

        view_kwargs = request.view_args if getattr(self.opts, 'view_kwargs', None) is True else dict()
        add_pagination_links(result.data,
                             object_count,
                             qs,
                             url_for(self.view, **view_kwargs))

        return result.data

    @check_method_requirements
    def post(self, *args, **kwargs):
        """Create an object
        """
        json_data = request.get_json()

        qs = QSManager(request.args, self.schema)

        schema = compute_schema(self.schema,
                                getattr(self.opts, 'schema_post_kwargs', dict()),
                                qs,
                                qs.include)

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

        obj = self.data_layer.create_object(data, **kwargs)

        return schema.dump(obj).data, 201


class ResourceDetail(with_metaclass(ResourceDetailMeta, Resource)):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Get object details
        """
        obj = self.data_layer.get_object(**kwargs)

        qs = QSManager(request.args, self.schema)

        schema = compute_schema(self.schema,
                                getattr(self.opts, 'schema_get_kwargs', dict()),
                                qs,
                                qs.include)

        result = schema.dump(obj)

        return result.data

    @check_method_requirements
    def patch(self, *args, **kwargs):
        """Update an object
        """
        json_data = request.get_json()

        qs = QSManager(request.args, self.schema)
        schema_kwargs = getattr(self.opts, 'schema_patch_kwargs', dict())
        schema_kwargs.update({'partial': True})

        schema = compute_schema(self.schema,
                                schema_kwargs,
                                qs,
                                qs.include)

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

        if 'id' not in json_data['data']:
            raise BadRequest('/data/id', 'Missing id in "data" node')
        if json_data['data']['id'] != str(kwargs[getattr(self.data_layer, 'url_field', 'id')]):
            raise BadRequest('/data/id', 'Value of id does not match the resource identifier in url')

        obj = self.data_layer.get_object(**kwargs)
        updated = self.data_layer.update_object(obj, data, **kwargs)

        result = schema.dump(obj)

        status_code = 200 if updated is True else 204
        return result.data, status_code

    @check_method_requirements
    def delete(self, *args, **kwargs):
        """Delete an object
        """
        obj = self.data_layer.get_object(**kwargs)
        self.data_layer.delete_object(obj, **kwargs)
        return 'Object successful deleted', 204


class ResourceRelationship(with_metaclass(ResourceRelationshipMeta, Resource)):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Get a relationship details
        """
        relationship_field, related_type_, related_id_field = self._get_relationship_data()
        related_view = self.schema._declared_fields[relationship_field].related_view
        related_view_kwargs = self.schema._declared_fields[relationship_field].related_view_kwargs

        obj, data = self.data_layer.get_relationship(relationship_field, related_type_, related_id_field, **kwargs)

        for key, value in copy(related_view_kwargs).items():
            if isinstance(value, str) and value.startswith('<') and value.endswith('>'):
                tmp_obj = obj
                for field in value[1:-1].split('.'):
                    tmp_obj = getattr(tmp_obj, field)
                related_view_kwargs[key] = tmp_obj

        result = {'links': {'self': url_for(self.view, **kwargs),
                            'related': url_for(related_view, **related_view_kwargs)},
                  'data': data}

        qs = QSManager(request.args, self.schema)
        if qs.include:
            schema = compute_schema(self.schema, dict(), qs, qs.include)

            serialized_obj = schema.dump(obj)
            result['included'] = serialized_obj.data.get('included', dict())

        return result

    @check_method_requirements
    def post(self, *args, **kwargs):
        """Add / create relationship(s)
        """
        json_data = request.get_json()

        relationship_field, related_type_, related_id_field = self._get_relationship_data()

        if 'data' not in json_data:
            raise BadRequest('/data', 'You must provide data with a "data" route node')
        if isinstance(json_data['data'], dict):
            if 'type' not in json_data['data']:
                raise BadRequest('/data/type', 'Missing type in "data" node')
            if 'id' not in json_data['data']:
                raise BadRequest('/data/id', 'Missing id in "data" node')
            if json_data['data']['type'] != related_type_:
                raise InvalidType('/data/type', 'The type field does not match the resource type')
        if isinstance(json_data['data'], list):
            for obj in json_data['data']:
                if 'type' not in obj:
                    raise BadRequest('/data/type', 'Missing type in "data" node')
                if 'id' not in obj:
                    raise BadRequest('/data/id', 'Missing id in "data" node')
                if obj['type'] != related_type_:
                    raise InvalidType('/data/type', 'The type provided does not match the resource type')

        obj_, updated = self.data_layer.create_relationship(json_data, relationship_field, related_id_field, **kwargs)

        qs = QSManager(request.args, self.schema)
        schema = compute_schema(self.schema, dict(), qs, qs.include)

        status_code = 200 if updated is True else 204

        return schema.dump(obj_), status_code

    @check_method_requirements
    def patch(self, *args, **kwargs):
        """Update a relationship
        """
        json_data = request.get_json()

        relationship_field, related_type_, related_id_field = self._get_relationship_data()

        if 'data' not in json_data:
            raise BadRequest('/data', 'You must provide data with a "data" route node')
        if isinstance(json_data['data'], dict):
            if 'type' not in json_data['data']:
                raise BadRequest('/data/type', 'Missing type in "data" node')
            if 'id' not in json_data['data']:
                raise BadRequest('/data/id', 'Missing id in "data" node')
            if json_data['data']['type'] != related_type_:
                raise InvalidType('/data/type', 'The type field does not match the resource type')
        if isinstance(json_data['data'], list):
            for obj in json_data['data']:
                if 'type' not in obj:
                    raise BadRequest('/data/type', 'Missing type in "data" node')
                if 'id' not in obj:
                    raise BadRequest('/data/id', 'Missing id in "data" node')
                if obj['type'] != related_type_:
                    raise InvalidType('/data/type', 'The type provided does not match the resource type')

        obj_, updated = self.data_layer.update_relationship(json_data, relationship_field, related_id_field, **kwargs)

        qs = QSManager(request.args, self.schema)
        schema = compute_schema(self.schema, dict(), qs, qs.include)

        status_code = 200 if updated is True else 204

        return schema.dump(obj_), status_code

    @check_method_requirements
    def delete(self, *args, **kwargs):
        """Delete relationship(s)
        """
        json_data = request.get_json()

        relationship_field, related_type_, related_id_field = self._get_relationship_data()

        if 'data' not in json_data:
            raise BadRequest('/data', 'You must provide data with a "data" route node')
        if isinstance(json_data['data'], dict):
            if 'type' not in json_data['data']:
                raise BadRequest('/data/type', 'Missing type in "data" node')
            if 'id' not in json_data['data']:
                raise BadRequest('/data/id', 'Missing id in "data" node')
            if json_data['data']['type'] != related_type_:
                raise InvalidType('/data/type', 'The type field does not match the resource type')
        if isinstance(json_data['data'], list):
            for obj in json_data['data']:
                if 'type' not in obj:
                    raise BadRequest('/data/type', 'Missing type in "data" node')
                if 'id' not in obj:
                    raise BadRequest('/data/id', 'Missing id in "data" node')
                if obj['type'] != related_type_:
                    raise InvalidType('/data/type', 'The type provided does not match the resource type')

        obj_, updated = self.data_layer.delete_relationship(json_data, relationship_field, related_id_field, **kwargs)

        qs = QSManager(request.args, self.schema)
        schema = compute_schema(self.schema, dict(), qs, qs.include)

        status_code = 200 if updated is True else 204

        return schema.dump(obj_), status_code

    def _get_relationship_data(self):
        """Get useful data for relationship management
        """
        relationship_field = request.base_url.split('/')[-1]

        if relationship_field not in get_relationships(self.schema):
            raise RelationNotFound('', "{} has no attribut {}".format(self.schema.__name__, relationship_field))

        related_type_ = self.schema._declared_fields[relationship_field].type_
        related_id_field = self.schema._declared_fields[relationship_field].id_field

        if hasattr(self.opts, 'schema_to_model') and\
                self.opts.schema_to_model.get(relationship_field) is not None:
            relationship_field = self.opts.schema_to_model[relationship_field]

        return relationship_field, related_type_, related_id_field
