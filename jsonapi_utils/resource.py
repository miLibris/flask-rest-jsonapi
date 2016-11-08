# -*- coding: utf-8 -*-

from six import with_metaclass

from flask import request, url_for
from flask.views import MethodViewType
from flask_restful import Resource
from marshmallow import ValidationError
from marshmallow_jsonapi.exceptions import IncorrectTypeError

from jsonapi_utils.data_layers.alchemy import SqlalchemyDataLayer
from jsonapi_utils.errors import ErrorFormatter
from jsonapi_utils.querystring import QueryStringManager as QSManager
from jsonapi_utils.marshmallow import paginate_result

DATA_LAYERS = {
    'sqlalchemy': SqlalchemyDataLayer
}


class ResourceMeta(MethodViewType):

    def __init__(cls, name, bases, nmspc):
        super(ResourceMeta, cls).__init__(name, bases, nmspc)
        meta = nmspc.get('Meta')

        if meta is not None:
            data_layer = getattr(meta, 'data_layer')

            if data_layer is None:
                raise Exception("You must provider a data layer")

            try:
                data_layer_cls = DATA_LAYERS[data_layer]
            except KeyError:
                raise Exception("data_layer not found")

            data_layer_kwargs = getattr(meta, 'data_layer_kwargs', {})

            cls.data_layer = data_layer_cls(**data_layer_kwargs)


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

            for get_decorator in get_decorators:
                cls.get = get_decorator(cls.get)

            for patch_decorator in patch_decorators:
                cls.patch = patch_decorator(cls.patch)


class ResourceList(with_metaclass(ResourceListMeta, Resource)):

    def get(self, *args, **kwargs):
        """
        """
        qs = QSManager(request.args)

        items = self.data_layer.get_items(self, qs, **kwargs)

        schema_kwargs = {}
        if qs.fields.get(self.resource_type):
            schema_kwargs = {'only': set(self.schema_cls._declared_fields.keys()) & set(qs.fields[self.resource_type])}
            schema_kwargs['only'].add('id')
        schema = self.schema_cls(many=True, **schema_kwargs)

        result = schema.dump(items)

        if hasattr(self, 'collection_endpoint_request_view_args')\
                and self.collection_endpoint_request_view_args is True:
            self.endpoint_kwargs = request.view_args
        else:
            self.endpoint_kwargs = {}
        paginate_result(result.data, len(items), qs, url_for(self.collection_endpoint, **self.endpoint_kwargs))

        return result.data

    def post(self, *args, **kwargs):
        """
        """
        json_data = request.get_json()

        schema = self.schema_cls()
        try:
            data, errors = schema.load(json_data)
        except ValidationError as err:
            return err.messages, 422
        except IncorrectTypeError as err:
            return err.messages, 409

        item = self.data_layer.create_and_save_item(data, self.before_create_instance, **kwargs)

        if json_data['data'].get('id') is not None:
            return '', 204
        else:
            return schema.dump(item).data


class ResourceDetail(with_metaclass(ResourceDetailMeta, Resource)):

    def get(self, *args, **kwargs):
        try:
            item = self.data_layer.get_item(**kwargs)
        except Exception as e:
            return ErrorFormatter.format_error(e.args), 404

        qs = QSManager(request.args)

        schema_kwargs = {}
        if qs.fields.get(self.resource_type):
            schema_kwargs = {'only': set(self.schema_cls._declared_fields.keys()) & set(qs.fields[self.resource_type])}
            schema_kwargs['only'].add('id')
        schema = self.schema_cls(**schema_kwargs)

        result = schema.dump(item)

        return result.data

    def patch(self, *args, **kwargs):
        json_data = request.get_json()

        schema = self.schema_cls(partial=True)
        try:
            data, errors = schema.load(json_data)
        except ValidationError as err:
            return err.messages, 422
        except IncorrectTypeError as err:
            return err.messages, 409

        try:
            if json_data['data']['id'] is None:
                raise KeyError
        except KeyError:
            return ErrorFormatter.format_error(["You must provide id of the entity"]), 422

        try:
            item = self.data_layer.get_item(**kwargs)
        except Exception as e:
            return ErrorFormatter.format_error(e.args), 404

        for field in schema.declared_fields.keys():
            if data.get(field):
                setattr(item, field, data[field])

        self.data_layer.persiste_update()

        return '', 204
