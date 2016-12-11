# -*- coding: utf-8 -*-

from flask_rest_jsonapi.resource import ResourceList


class Api(object):

    def __init__(self, blueprint):
        """Initialize the api

        :param blueprint (Blueprint): a flask blueprint instance
        """
        self.blueprint = blueprint

    def add_list_route(self, url, resource_cls=None, resource_type=None, schema=None, endpoint=None,
                       get_decorators=None, post_decorators=None, data_layer=None, disabled_methods=None, options=None):
        """Create endpoint to retrieve a list of item or to create one.

        :param url (str): the url of the endpoint
        :param resource_cls (callable): a resource class like flask.MethodView
        :param resource_type (str): the name of the collection
        :param schema (dict): information about marshallow schema
        :param endpoint (dict): information about endpoint
        :param get_decorators (list): a list of decorator for the get method
        :param post_decorators (list): a list of decorator for the post method
        :param data_layer (dict): information about the data layer
        :param disabled_methods (list): list of methods to disable
        """

        resource_cls_kwargs = {}
        if resource_type is not None:
            resource_cls_kwargs['resource_type'] = resource_type
        if schema is not None:
            resource_cls_kwargs['schema'] = schema
        if endpoint is not None:
            endpoint['full_endpoint'] = ".".join([self.blueprint.name, endpoint['alias']])
            resource_cls_kwargs['endpoint'] = endpoint

        meta = None
        if get_decorators is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'get_decorators', get_decorators)
        if post_decorators is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'post_decorators', post_decorators)
        if data_layer is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'data_layer', data_layer)
        if disabled_methods is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'disabled_methods', disabled_methods)
        if meta is not None:
            resource_cls_kwargs['Meta'] = meta

        resource_cls = resource_cls or type("%sResourceList" % resource_type, (ResourceList, ), resource_cls_kwargs)

        options = options or dict()

        self.blueprint.add_url_rule(url, view_func=resource_cls.as_view(endpoint.get('alias')), **options)

    def add_detail_route(self, url, resource_cls=None, resource_type=None, schema=None, endpoint=None,
                         get_decorators=None, patch_decorators=None, delete_decorators=None, data_layer=None,
                         disabled_methods=None, options=None):
        """Create endpoint to retrieve a list of item or to create one.

        :param url (str): the url of the endpoint
        :param resource_cls (callable): a resource class like flask.MethodView
        :param resource_type (str): the name of the collection
        :param schema (dict): information about marshallow schema
        :param endpoint (dict): information about endpoint
        :param get_decorators (list): a list of decorator for the get method
        :param post_decorators (list): a list of decorator for the post method
        :param data_layer (dict): information about the data layer
        :param disabled_methods (list): list of methods to disable
        """

        resource_cls_kwargs = {}
        if resource_type is not None:
            resource_cls_kwargs['resource_type'] = resource_type
        if schema is not None:
            resource_cls_kwargs['schema'] = schema

        meta = None
        if get_decorators is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'get_decorators', get_decorators)
        if patch_decorators is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'patch_decorators', patch_decorators)
        if delete_decorators is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'delete_decorators', delete_decorators)
        if data_layer is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'data_layer', data_layer)
        if disabled_methods is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'disabled_methods', disabled_methods)
        if meta is not None:
            resource_cls_kwargs['Meta'] = meta

        resource_cls = resource_cls or type("%sResourceList" % resource_type, (ResourceList, ), resource_cls_kwargs)

        options = options or dict()

        self.blueprint.add_url_rule(url, view_func=resource_cls.as_view(endpoint), **options)

    def init_app(self, app):
        """Update flask application with our api

        :param app (Application): a flask application
        """
        app.register_blueprint(self.blueprint)
