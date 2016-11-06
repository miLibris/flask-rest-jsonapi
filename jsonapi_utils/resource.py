# -*- coding: utf-8 -*-

from six import with_metaclass

from flask.views import MethodViewType
from flask_restful import Resource

from jsonapi_utils.helpers import jsonapi_detail, jsonapi_update


class ResourceDetailMeta(MethodViewType):

    def __init__(cls, name, bases, nmspc):
        super(ResourceDetailMeta, cls).__init__(name, bases, nmspc)
        meta = nmspc.get('Meta')

        get_decorators = getattr(meta, 'get_decorators', [])
        patch_decorators = getattr(meta, 'patch_decorators', [])

        for get_decorator in get_decorators:
            cls.get = get_decorator(cls.get)

        for patch_decorator in patch_decorators:
            cls.patch = patch_decorator(cls.patch)


class ResourceDetail(with_metaclass(ResourceDetailMeta, Resource)):

    def get(self, *args, **kwargs):
        return jsonapi_detail(self.type_,
                              self.schema_kls,
                              self.model,
                              self.key,
                              str(kwargs[self.url_key]),
                              self.db_session_factory.session)

    def patch(self, *args, **kwargs):
        return jsonapi_update(self.schema_kls,
                              self.model,
                              self.key,
                              str(kwargs[self.url_key]),
                              self.db_session_factory.session)
