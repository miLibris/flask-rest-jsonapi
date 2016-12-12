# -*- coding: utf-8 -*-

from flask import Blueprint
from flask_rest_jsonapi.resource import ResourceList, ResourceDetail


class Api(object):

    def __init__(self, app=None):
        self.app = None
        self.blueprint = None

        if app is not None:
            if isinstance(app, Blueprint):
                self.blueprint = app
            else:
                self.app = app

        self.resources = []

    def list_route(self, endpoint, *urls, **kwargs):
        """Create endpoint to retrieve a list of item or to create one.

        :param endpoint (str): the endpoint name
        :param urls (list): the urls of the endpoint
        :param resource_cls (ResourceList): a resource class like flask.MethodView
        :param resource_type (str): the name of the collection
        :param schema (Schema): a marshallow schema class
        :param schema_get_kwargs (dict): schema kwargs for get method
        :param schema_post_kwargs (dict): schema kwargs for post method
        :param data_layer (BaseDataLayer): a the data layer class
        :param data_layer_kwargs (dict): the data layer kwargs
        :param data_layer_additional_functions (dict): the data layer additional functions
        :param get_decorators (list): a list of decorator for the get method
        :param post_decorators (list): a list of decorator for the post method
        :param disabled_methods (list): list of methods to disable
        :param url_rule_options (dict): additional parameters for flask.Flask.add_url_rule
        :param endpoint_include_view_kwargs (boolean): a flag that indicate to include view kwargs to the context of
                                                       flask.url_for
        """
        self._register_resource('list', endpoint, urls, kwargs)

    def detail_route(self, endpoint, *urls, **kwargs):
        """Create endpoint to retrieve a list of item or to create one.

        :param endpoint (str): the endpoint name
        :param urls (list): the urls of the endpoint
        :param resource_cls (ResourceList): a resource class like flask.MethodView
        :param resource_type (str): the name of the collection
        :param schema (Schema): a marshallow schema class
        :param schema_get_kwargs (dict): schema kwargs for get method
        :param schema_post_kwargs (dict): schema kwargs for post method
        :param data_layer (BaseDataLayer): a the data layer class
        :param data_layer_kwargs (dict): the data layer kwargs
        :param data_layer_additional_functions (dict): the data layer additional functions
        :param get_decorators (list): a list of decorator for the get method
        :param patch_decorators (list): a list of decorator for the patch method
        :param delete_decorators (list): a list of decorator for the delete method
        :param disabled_methods (list): list of methods to disable
        :param url_rule_options (dict): additional parameters for flask.Flask.add_url_rule
        """
        self._register_resource('detail', endpoint, urls, kwargs)

    def init_app(self, app):
        """Update flask application with our api

        :param app (Application): a flask application
        """
        if self.blueprint is not None:
            app.register_blueprint(self.blueprint)
        else:
            self.app = app
            for resource in self.resources:
                self._register_route(**resource)

    def _register_resource(self, kind, endpoint, urls, kwargs):
        """Register a resource in api

        :param kind (str): the kind of the resource (list or detail)
        :param endpoint (str): the endpoint name
        :param urls (list): the urls of the endpoint
        :param kwargs (dict): route kwargs
        """
        resource_cls = self._build_resource_cls(kind, endpoint, kwargs)

        options = kwargs.get('url_rule_options') or dict()
        self._register_route(resource_cls, endpoint, options, urls)

    def _build_resource_cls(self, kind, endpoint, kwargs):
        """Build a resource class

        :param kind (str): the kind of the resource (list or detail)
        :param endpoint (str): the endpoint name
        :param kwargs (dict): route kwargs
        """
        resource_kwargs = self._get_resource_kwargs(endpoint, kwargs)

        default_resource_cls = {'list': ResourceList, 'detail': ResourceDetail}[kind]

        resource_cls = kwargs.get('resource_cls') or type("%sResourceList" % kwargs['resource_type'].capitalize(),
                                                          (default_resource_cls, ),
                                                          resource_kwargs)

        return resource_cls

    def _get_resource_kwargs(self, endpoint, kwargs):
        """Get kwargs from route kwargs

        :param endpoint (str): the endpoint name
        :param kwargs (dict): route kwargs
        """
        resource_kwargs = {}

        if kwargs.get('resource_type') is not None:
            resource_kwargs['resource_type'] = kwargs['resource_type']

        if kwargs.get('schema') is not None:
            resource_kwargs['schema'] = {'cls': kwargs['schema']}
            if kwargs.get('schema_get_kwargs') is not None:
                resource_kwargs['schema'].update({'get_kwargs': kwargs['schema_get_kwargs']})
            if kwargs.get('schema_post_kwargs') is not None:
                resource_kwargs['schema'].update({'post_kwargs': kwargs['schema_post_kwargs']})

        if self.blueprint is not None and self.blueprint.name is not None:
            endpoint = '.'.join([self.blueprint.name, endpoint])
        resource_kwargs['endpoint'] = {'name': endpoint}
        if kwargs.get('endpoint_include_view_kwargs') is not None:
            resource_kwargs['endpoint'].update({'include_view_kwargs': kwargs['endpoint_include_view_kwargs']})

        meta = None

        if kwargs.get('data_layer') is not None:
            meta = meta or type('Meta', (), {})
            data_layer = {'cls': kwargs['data_layer']}
            if kwargs.get('data_layer_kwargs') is not None:
                data_layer.update({'kwargs': kwargs['data_layer_kwargs']})
            if kwargs.get('data_layer_additional_functions') is not None:
                data_layer.update(kwargs['data_layer_additional_functions'])
            setattr(meta, 'data_layer', data_layer)

        if kwargs.get('get_decorators') is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'get_decorators', kwargs['get_decorators'])

        if kwargs.get('post_decorators') is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'post_decorators', kwargs['post_decorators'])

        if kwargs.get('patch_decorators') is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'patch_decorators', kwargs['patch_decorators'])

        if kwargs.get('delete_decorators') is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'delete_decorators', kwargs['delete_decorators'])

        if kwargs.get('disabled_methods') is not None:
            meta = meta or type('Meta', (), {})
            setattr(meta, 'disabled_methods', kwargs['disabled_methods'])

        if meta is not None:
            resource_kwargs['Meta'] = meta

        return resource_kwargs

    def _register_route(self, resource_cls, endpoint, options, urls):
        """Register url

        :param resource_cls (Resource): a resource class
        :param endpoint (str): the endpoint name
        :options (dict): options for flask.add_url_rule
        :param urls (list): the urls of the endpoint
        """
        view_func = resource_cls.as_view(endpoint)
        if self.app is not None:
            for url in urls:
                self.app.add_url_rule(url, view_func=view_func, **options)
        elif self.blueprint is not None:
            for url in urls:
                self.blueprint.add_url_rule(url, view_func=view_func, **options)
        else:
            self.resources.append({'resource_cls': resource_cls,
                                   'endpoint': endpoint,
                                   'options': options,
                                   'urls': urls})
