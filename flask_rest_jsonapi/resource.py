# -*- coding: utf-8 -*-

import inspect
import json
from copy import copy

from werkzeug.wrappers import Response
from flask import request, url_for, make_response, current_app
from flask.views import MethodView
from marshmallow_jsonapi.exceptions import IncorrectTypeError
from marshmallow import ValidationError

from flask_rest_jsonapi.errors import jsonapi_errors
from flask_rest_jsonapi.querystring import QueryStringManager as QSManager
from flask_rest_jsonapi.pagination import add_pagination_links
from flask_rest_jsonapi.exceptions import InvalidType, BadRequest, JsonApiException, RelationNotFound
from flask_rest_jsonapi.decorators import check_headers, check_method_requirements, add_headers
from flask_rest_jsonapi.schema import compute_schema, get_relationships
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.data_layers.alchemy import SqlalchemyDataLayer


class Resource(MethodView):

    def __new__(cls):
        if hasattr(cls, 'data_layer'):
            if not isinstance(cls.data_layer, dict):
                raise Exception("You must provide a data layer information as dict in {}".format(cls.__name__))

            if cls.data_layer.get('class') is not None and BaseDataLayer not in inspect.getmro(cls.data_layer['class']):
                raise Exception("You must provide a data layer class inherited from BaseDataLayer in {}"
                                .format(cls.__name__))

            data_layer_cls = cls.data_layer.get('class', SqlalchemyDataLayer)
            cls._data_layer = data_layer_cls(**cls.data_layer)
            cls._data_layer.resource = cls

        for method in ('get', 'post', 'patch', 'delete'):
            if hasattr(cls, '{}_decorators'.format(method)) and hasattr(cls, method):
                for decorator in getattr(cls, '{}_decorators'.format(method)):
                    setattr(cls, method, decorator(getattr(cls, method)))

        return super(Resource, cls).__new__(cls)

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
        except Exception as e:
            if current_app.config['DEBUG'] is True:
                raise e
            exc = JsonApiException('', str(e))
            return make_response(json.dumps(jsonapi_errors([exc.to_dict()])),
                                 exc.status,
                                 {'Content-Type': 'application/vnd.api+json'})

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


class ResourceList(Resource):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Retrieve a collection of objects
        """
        self.before_get(*args, **kwargs)

        qs = QSManager(request.args, self.schema)
        object_count, objects = self._data_layer.get_collection(qs, **kwargs)

        schema_kwargs = getattr(self, 'get_schema_kwargs', dict())
        schema_kwargs.update({'many': True})

        schema = compute_schema(self.schema,
                                schema_kwargs,
                                qs,
                                qs.include)

        result = schema.dump(objects).data

        view_kwargs = request.view_args if getattr(self, 'view_kwargs', None) is True else dict()
        add_pagination_links(result,
                             object_count,
                             qs,
                             url_for(self.view, **view_kwargs))

        self.after_get(result)
        return result

    @check_method_requirements
    def post(self, *args, **kwargs):
        """Create an object
        """
        self.before_post(*args, **kwargs)

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

        obj = self._data_layer.create_object(data, **kwargs)

        result = schema.dump(obj).data
        self.after_post(result)
        return result, 201

    def before_get(self, *args, **kwargs):
        pass

    def after_get(self, result):
        pass

    def before_post(self, *args, **kwargs):
        pass

    def after_post(self, result):
        pass


class ResourceDetail(Resource):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Get object details
        """
        self.before_get(*args, **kwargs)

        obj = self._data_layer.get_object(**kwargs)

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
        self.before_patch(*args, **kwargs)

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

        obj = self._data_layer.get_object(**kwargs)
        updated = self._data_layer.update_object(obj, data, **kwargs)

        result = schema.dump(obj).data

        status_code = 200 if updated is True else 204
        self.after_patch(result)
        return result, status_code

    @check_method_requirements
    def delete(self, *args, **kwargs):
        """Delete an object
        """
        self.before_delete(*args, **kwargs)

        obj = self._data_layer.get_object(**kwargs)
        self._data_layer.delete_object(obj, **kwargs)

        result = {'meta': 'Object successful deleted'}
        self.after_delete(result)
        return result, 204

    def before_get(self, *args, **kwargs):
        pass

    def after_get(self, result):
        pass

    def before_patch(self, *args, **kwargs):
        pass

    def after_patch(self, result):
        pass

    def before_delete(self, *args, **kwargs):
        pass

    def after_delete(self, result):
        pass


class ResourceRelationship(Resource):

    @check_method_requirements
    def get(self, *args, **kwargs):
        """Get a relationship details
        """
        self.before_get(*args, **kwargs)

        relationship_field, model_relationship_field, related_type_, related_id_field = self._get_relationship_data()
        related_view = self.schema._declared_fields[relationship_field].related_view
        related_view_kwargs = self.schema._declared_fields[relationship_field].related_view_kwargs

        obj, data = self._data_layer.get_relationship(model_relationship_field,
                                                      related_type_,
                                                      related_id_field,
                                                      **kwargs)

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

        self.after_get(result)
        return result

    @check_method_requirements
    def post(self, *args, **kwargs):
        """Add / create relationship(s)
        """
        self.before_post(*args, **kwargs)

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
                                                             **kwargs)

        qs = QSManager(request.args, self.schema)
        schema = compute_schema(self.schema, dict(), qs, qs.include)

        status_code = 200 if updated is True else 204
        result = schema.dump(obj_).data
        self.after_post(result)
        return result, status_code

    @check_method_requirements
    def patch(self, *args, **kwargs):
        """Update a relationship
        """
        self.before_patch(*args, **kwargs)

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
                                                             **kwargs)

        qs = QSManager(request.args, self.schema)
        schema = compute_schema(self.schema, dict(), qs, qs.include)

        status_code = 200 if updated is True else 204
        result = schema.dump(obj_).data
        self.after_patch(result)
        return result, status_code

    @check_method_requirements
    def delete(self, *args, **kwargs):
        """Delete relationship(s)
        """
        self.before_delete(*args, **kwargs)

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
                                                             **kwargs)

        qs = QSManager(request.args, self.schema)
        schema = compute_schema(self.schema, dict(), qs, qs.include)

        status_code = 200 if updated is True else 204
        result = schema.dump(obj_).data
        self.after_delete(result)
        return result, status_code

    def _get_relationship_data(self):
        """Get useful data for relationship management
        """
        relationship_field = request.base_url.split('/')[-1]

        if relationship_field not in get_relationships(self.schema):
            raise RelationNotFound('', "{} has no attribut {}".format(self.schema.__name__, relationship_field))

        related_type_ = self.schema._declared_fields[relationship_field].type_
        related_id_field = self.schema._declared_fields[relationship_field].id_field

        if hasattr(self, 'schema_to_model') and self.schema_to_model.get(relationship_field) is not None:
            model_relationship_field = self.schema_to_model[relationship_field]
        else:
            model_relationship_field = relationship_field

        return relationship_field, model_relationship_field, related_type_, related_id_field

    def before_get(self, *args, **kwargs):
        pass

    def after_get(self, result):
        pass

    def before_post(self, *args, **kwargs):
        pass

    def after_post(self, result):
        pass

    def before_patch(self, *args, **kwargs):
        pass

    def after_patch(self, result):
        pass

    def before_delete(self, *args, **kwargs):
        pass

    def after_delete(self, result):
        pass
