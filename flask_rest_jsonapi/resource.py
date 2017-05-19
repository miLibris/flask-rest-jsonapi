# -*- coding: utf-8 -*-

import inspect
import json
from copy import copy
from six import with_metaclass

from werkzeug.wrappers import Response
from flask import request, url_for, make_response, current_app
from flask.views import MethodView, MethodViewType
from marshmallow_jsonapi.exceptions import IncorrectTypeError
from marshmallow import ValidationError

from flask_rest_jsonapi.errors import jsonapi_errors
from flask_rest_jsonapi.querystring import QueryStringManager as QSManager
from flask_rest_jsonapi.pagination import add_pagination_links
from flask_rest_jsonapi.exceptions import InvalidType, BadRequest, JsonApiException, RelationNotFound
from flask_rest_jsonapi.decorators import check_headers, check_method_requirements
from flask_rest_jsonapi.schema import compute_schema, get_relationships, get_model_field
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.data_layers.alchemy import SqlalchemyDataLayer


class ResourceMeta(MethodViewType):

    def __new__(cls, name, bases, d):
        rv = super(ResourceMeta, cls).__new__(cls, name, bases, d)
        if 'data_layer' in d:
            if not isinstance(d['data_layer'], dict):
                raise Exception("You must provide a data layer information as dict in {}".format(cls.__name__))

            if d['data_layer'].get('class') is not None\
                    and BaseDataLayer not in inspect.getmro(d['data_layer']['class']):
                raise Exception("You must provide a data layer class inherited from BaseDataLayer in {}"
                                .format(cls.__name__))

            data_layer_cls = d['data_layer'].get('class', SqlalchemyDataLayer)
            data_layer_kwargs = d['data_layer']
            rv._data_layer = data_layer_cls(data_layer_kwargs)

        rv.decorators = (check_headers,)
        if 'decorators' in d:
            rv.decorators += d['decorators']

        return rv


class Resource(MethodView):

    def __new__(cls):
        if hasattr(cls, '_data_layer'):
            cls._data_layer.resource = cls

        return super(Resource, cls).__new__(cls)

    def dispatch_request(self, *args, **kwargs):
        method = getattr(self, request.method.lower(), None)
        if method is None and request.method == 'HEAD':
            method = getattr(self, 'get', None)
        assert method is not None, 'Unimplemented method {}'.format(request.method)

        headers = {'Content-Type': 'application/vnd.api+json'}

        try:
            response = method(*args, **kwargs)
        except JsonApiException as e:
            return make_response(json.dumps(jsonapi_errors([e.to_dict()])),
                                 e.status,
                                 headers)
        except Exception as e:
            if current_app.config['DEBUG'] is True:
                raise e
            exc = JsonApiException('', str(e))
            return make_response(json.dumps(jsonapi_errors([exc.to_dict()])),
                                 exc.status,
                                 headers)

        if isinstance(response, Response):
            response.headers.add('Content-Type', 'application/vnd.api+json')
            return response

        if not isinstance(response, tuple):
            if isinstance(response, dict):
                response.update({'jsonapi': {'version': '1.0'}})
            return make_response(json.dumps(response), 200, headers)

        try:
            data, status_code, headers = response
            headers.update({'Content-Type': 'application/vnd.api+json'})
        except ValueError:
            pass

        try:
            data, status_code = response
        except ValueError:
            pass

        if isinstance(data, dict):
            data.update({'jsonapi': {'version': '1.0'}})

        return make_response(json.dumps(data), status_code, headers)


class ResourceList(with_metaclass(ResourceMeta, Resource)):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Retrieve a collection of objects
        """
        self.before_get(args, kwargs)

        qs = QSManager(request.args, self.schema)
        objects_count, objects = self._data_layer.get_collection(qs, kwargs)

        schema_kwargs = getattr(self, 'get_schema_kwargs', dict())
        schema_kwargs.update({'many': True})

        schema = compute_schema(self.schema,
                                schema_kwargs,
                                qs,
                                qs.include)

        result = schema.dump(objects).data

        view_kwargs = request.view_args if getattr(self, 'view_kwargs', None) is True else dict()
        add_pagination_links(result,
                             objects_count,
                             qs,
                             url_for(self.view, **view_kwargs))

        result.update({'meta': {'count': objects_count}})

        self.after_get(result)
        return result

    @check_method_requirements
    def post(self, *args, **kwargs):
        """Create an object
        """
        self.before_post(args, kwargs)

        json_data = request.get_json()

        qs = QSManager(request.args, self.schema)

        schema = compute_schema(self.schema,
                                getattr(self, 'post_schema_kwargs', dict()),
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

        obj = self._data_layer.create_object(data, kwargs)

        result = schema.dump(obj).data
        self.after_post(result)
        return result, 201, {'Location': result['data']['links']['self']}

    def before_get(self, args, kwargs):
        pass

    def after_get(self, result):
        pass

    def before_post(self, args, kwargs):
        pass

    def after_post(self, result):
        pass


class ResourceDetail(with_metaclass(ResourceMeta, Resource)):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Get object details
        """
        self.before_get(args, kwargs)

        obj = self._data_layer.get_object(kwargs)

        qs = QSManager(request.args, self.schema)

        schema = compute_schema(self.schema,
                                getattr(self, 'get_schema_kwargs', dict()),
                                qs,
                                qs.include)

        result = schema.dump(obj).data

        self.after_get(result)
        return result

    @check_method_requirements
    def patch(self, *args, **kwargs):
        """Update an object
        """
        self.before_patch(args, kwargs)

        json_data = request.get_json()

        qs = QSManager(request.args, self.schema)
        schema_kwargs = getattr(self, 'patch_schema_kwargs', dict())
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
        if json_data['data']['id'] != str(kwargs[self.data_layer.get('url_field', 'id')]):
            raise BadRequest('/data/id', 'Value of id does not match the resource identifier in url')

        obj = self._data_layer.get_object(kwargs)
        self._data_layer.update_object(obj, data, kwargs)

        result = schema.dump(obj).data

        self.after_patch(result)
        return result

    @check_method_requirements
    def delete(self, *args, **kwargs):
        """Delete an object
        """
        self.before_delete(args, kwargs)

        obj = self._data_layer.get_object(kwargs)
        self._data_layer.delete_object(obj, kwargs)

        result = {'meta': {'message': 'Object successfully deleted'}}
        self.after_delete(result)
        return result

    def before_get(self, args, kwargs):
        pass

    def after_get(self, result):
        pass

    def before_patch(self, args, kwargs):
        pass

    def after_patch(self, result):
        pass

    def before_delete(self, args, kwargs):
        pass

    def after_delete(self, result):
        pass


class ResourceRelationship(with_metaclass(ResourceMeta, Resource)):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Get a relationship details
        """
        self.before_get(args, kwargs)

        relationship_field, model_relationship_field, related_type_, related_id_field = self._get_relationship_data()
        related_view = self.schema._declared_fields[relationship_field].related_view
        related_view_kwargs = self.schema._declared_fields[relationship_field].related_view_kwargs

        obj, data = self._data_layer.get_relationship(model_relationship_field,
                                                      related_type_,
                                                      related_id_field,
                                                      kwargs)

        for key, value in copy(related_view_kwargs).items():
            if isinstance(value, str) and value.startswith('<') and value.endswith('>'):
                tmp_obj = obj
                for field in value[1:-1].split('.'):
                    tmp_obj = getattr(tmp_obj, field)
                related_view_kwargs[key] = tmp_obj

        result = {'links': {'self': request.path,
                            'related': url_for(related_view, **related_view_kwargs)},
                  'data': data}

        qs = QSManager(request.args, self.schema)
        if qs.include:
            schema = compute_schema(self.schema, dict(), qs, qs.include)

            serialized_obj = schema.dump(obj)
            result['included'] = serialized_obj.data.get('included', dict())

        self.after_get(result)
        return result

    @check_method_requirements
    def post(self, *args, **kwargs):
        """Add / create relationship(s)
        """
        self.before_post(args, kwargs)

        json_data = request.get_json()

        relationship_field, model_relationship_field, related_type_, related_id_field = self._get_relationship_data()

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

        obj_, updated = self._data_layer.create_relationship(json_data,
                                                             model_relationship_field,
                                                             related_id_field,
                                                             kwargs)

        qs = QSManager(request.args, self.schema)
        includes = qs.include
        if relationship_field not in qs.include:
            includes.append(relationship_field)
        schema = compute_schema(self.schema, dict(), qs, includes)

        if updated is False:
            return '', 204

        result = schema.dump(obj_).data
        if result.get('links', {}).get('self') is not None:
            result['links']['self'] = request.path
        self.after_post(result)
        return result, 200

    @check_method_requirements
    def patch(self, *args, **kwargs):
        """Update a relationship
        """
        self.before_patch(args, kwargs)

        json_data = request.get_json()

        relationship_field, model_relationship_field, related_type_, related_id_field = self._get_relationship_data()

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

        obj_, updated = self._data_layer.update_relationship(json_data,
                                                             model_relationship_field,
                                                             related_id_field,
                                                             kwargs)

        qs = QSManager(request.args, self.schema)
        includes = qs.include
        if relationship_field not in qs.include:
            includes.append(relationship_field)
        schema = compute_schema(self.schema, dict(), qs, includes)

        if updated is False:
            return '', 204

        result = schema.dump(obj_).data
        if result.get('links', {}).get('self') is not None:
            result['links']['self'] = request.path
        self.after_patch(result)
        return result, 200

    @check_method_requirements
    def delete(self, *args, **kwargs):
        """Delete relationship(s)
        """
        self.before_delete(args, kwargs)

        json_data = request.get_json()

        relationship_field, model_relationship_field, related_type_, related_id_field = self._get_relationship_data()

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

        obj_, updated = self._data_layer.delete_relationship(json_data,
                                                             model_relationship_field,
                                                             related_id_field,
                                                             kwargs)

        qs = QSManager(request.args, self.schema)
        includes = qs.include
        if relationship_field not in qs.include:
            includes.append(relationship_field)
        schema = compute_schema(self.schema, dict(), qs, includes)

        status_code = 200 if updated is True else 204
        result = schema.dump(obj_).data
        if result.get('links', {}).get('self') is not None:
            result['links']['self'] = request.path
        self.after_delete(result)
        return result, status_code

    def _get_relationship_data(self):
        """Get useful data for relationship management
        """
        relationship_field = request.path.split('/')[-1]

        if relationship_field not in get_relationships(self.schema).values():
            raise RelationNotFound('', "{} has no attribute {}".format(self.schema.__name__, relationship_field))

        related_type_ = self.schema._declared_fields[relationship_field].type_
        related_id_field = self.schema._declared_fields[relationship_field].id_field
        model_relationship_field = get_model_field(self.schema, relationship_field)

        return relationship_field, model_relationship_field, related_type_, related_id_field

    def before_get(self, args, kwargs):
        pass

    def after_get(self, result):
        pass

    def before_post(self, args, kwargs):
        pass

    def after_post(self, result):
        pass

    def before_patch(self, args, kwargs):
        pass

    def after_patch(self, result):
        pass

    def before_delete(self, args, kwargs):
        pass

    def after_delete(self, result):
        pass
