# -*- coding: utf-8 -*-

"""This module contains the main class of the Api to initialize the Api, plug default decorators for each resources
methods, speficy which blueprint to use, define the Api routes and plug additional oauth manager and permission manager
"""

import inspect
from functools import wraps

from flask import request, abort

from flask_rest_jsonapi.resource import ResourceList, ResourceRelationship
from flask_rest_jsonapi.decorators import jsonapi_exception_formatter


class Api(object):
    """The main class of the Api"""

    def __init__(self, app=None, blueprint=None, decorators=None):
        """Initialize an instance of the Api

        :param app: the flask application
        :param blueprint: a flask blueprint
        :param tuple decorators: a tuple of decorators plugged to each resource methods
        """
        self.app = app
        self.blueprint = blueprint
        self.resources = []
        self.resource_registry = []
        self.decorators = decorators or tuple()

        if app is not None:
            self.init_app(app, blueprint)

    def init_app(self, app=None, blueprint=None, additional_blueprints=None):
        """Update flask application with our api

        :param Application app: a flask application
        """
        if app is not None:
            self.app = app

        if blueprint is not None:
            self.blueprint = blueprint

        for resource in self.resources:
            self.route(resource['resource'],
                       resource['view'],
                       *resource['urls'],
                       url_rule_options=resource['url_rule_options'])

        if self.blueprint is not None:
            self.app.register_blueprint(self.blueprint)

        if additional_blueprints is not None:
            for blueprint in additional_blueprints:
                self.app.register_blueprint(blueprint)

        self.app.config.setdefault('PAGE_SIZE', 30)

    def route(self, resource, view, *urls, **kwargs):
        """Create an api view.

        :param Resource resource: a resource class inherited from flask_rest_jsonapi.resource.Resource
        :param str view: the view name
        :param list urls: the urls of the view
        :param dict kwargs: additional options of the route
        """
        resource.view = view
        url_rule_options = kwargs.get('url_rule_options') or dict()

        # Allow the customization of the resource class instance
        resource_args = kwargs.get('resource_args', [])
        resource_kwargs = kwargs.get('resource_kwargs', {})

        view_func = resource.as_view(view, *resource_args, **resource_kwargs)

        if 'blueprint' in kwargs:
            resource.view = '.'.join([kwargs['blueprint'].name, resource.view])
            for url in urls:
                kwargs['blueprint'].add_url_rule(url, view_func=view_func, **url_rule_options)
        elif self.blueprint is not None:
            resource.view = '.'.join([self.blueprint.name, resource.view])
            for url in urls:
                self.blueprint.add_url_rule(url, view_func=view_func, **url_rule_options)
        elif self.app is not None:
            for url in urls:
                self.app.add_url_rule(url, view_func=view_func, **url_rule_options)
        else:
            self.resources.append({'resource': resource,
                                   'view': view,
                                   'urls': urls,
                                   'url_rule_options': url_rule_options})

        self.resource_registry.append(resource)

    def oauth_manager(self, oauth_manager):
        """Use the oauth manager to enable oauth for API

        :param oauth_manager: the oauth manager
        """
        @self.app.before_request
        @jsonapi_exception_formatter
        def before_request():
            endpoint = request.endpoint
            resource = None
            if endpoint:
                resource = getattr(self.app.view_functions[endpoint], 'view_class', None)

            if resource and not getattr(resource, 'disable_oauth', None):
                scopes = request.args.get('scopes')

                if getattr(resource, 'schema'):
                    scopes = [self.build_scope(resource, request.method)]
                elif scopes:
                    scopes = scopes.split(',')

                    if scopes:
                        scopes = scopes.split(',')

                valid, req = oauth_manager.verify_request(scopes)

                for func in oauth_manager._after_request_funcs:
                    valid, req = func(valid, req)

                if not valid:
                    if oauth_manager._invalid_response:
                        return oauth_manager._invalid_response(req)
                    return abort(401)

                request.oauth = req

    @staticmethod
    def build_scope(resource, method):
        """Compute the name of the scope for oauth

        :param Resource resource: the resource manager
        :param str method: an http method
        :return str: the name of the scope
        """
        if ResourceList in inspect.getmro(resource) and method == 'GET':
            prefix = 'list'
        else:
            method_to_prefix = {'GET': 'get',
                                'POST': 'create',
                                'PATCH': 'update',
                                'DELETE': 'delete'}
            prefix = method_to_prefix[method]

            if ResourceRelationship in inspect.getmro(resource):
                prefix = '_'.join([prefix, 'relationship'])

        return '_'.join([prefix, resource.schema.opts.type_])

    def permission_manager(self, permission_manager, with_decorators=True):
        """Use permission manager to enable permission for API

        :param callable permission_manager: the permission manager
        """
        self.check_permissions = permission_manager

        if with_decorators:
            for resource in self.resource_registry:
                if getattr(resource, 'disable_permission', None) is not True:
                    for method in getattr(resource, 'methods', ('GET', 'POST', 'PATCH', 'DELETE')):
                        setattr(resource,
                                method.lower(),
                                self.has_permission()(getattr(resource, method.lower())))

    def has_permission(self, *args, **kwargs):
        """Decorator used to check permissions before to call resource manager method"""
        def wrapper(view):
            if getattr(view, '_has_permissions_decorator', False) is True:
                return view

            @wraps(view)
            @jsonapi_exception_formatter
            def decorated(*view_args, **view_kwargs):
                self.check_permissions(view, view_args, view_kwargs, *args, **kwargs)
                return view(*view_args, **view_kwargs)
            decorated._has_permissions_decorator = True
            return decorated
        return wrapper

    @staticmethod
    def check_permissions(view, view_args, view_kwargs, *args, **kwargs):
        """The function use to check permissions

        :param callable view: the view
        :param list view_args: view args
        :param dict view_kwargs: view kwargs
        :param list args: decorator args
        :param dict kwargs: decorator kwargs
        """
        raise NotImplementedError
