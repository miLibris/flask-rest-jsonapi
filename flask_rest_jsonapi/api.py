# -*- coding: utf-8 -*-

from flask import Blueprint


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

    def init_app(self, app=None):
        """Update flask application with our api

        :param Application app: a flask application
        """
        if self.app is None:
            self.app = app

        if self.blueprint is not None:
            self.app.register_blueprint(self.blueprint)
        else:
            for resource in self.resources:
                self.route(**resource)

    def route(self, resource, view, *urls, **kwargs):
        """Create an api view.

        :param Resource resource: a resource class inherited from flask_rest_jsonapi.resource.Resource
        :param str view: the view name
        :param list urls: the urls of the view
        :param dict kwargs: additional options of the route
        """
        resource.view = view
        view_func = resource.as_view(view)
        url_rule_options = kwargs.get('url_rule_options') or dict()

        if self.app is not None:
            for url in urls:
                self.app.add_url_rule(url, view_func=view_func, **url_rule_options)
        elif self.blueprint is not None:
            resource.view = '.'.join([self.blueprint.name, resource.view])
            for url in urls:
                self.blueprint.add_url_rule(url, view_func=view_func, **url_rule_options)
        else:
            self.resources.append({'resource': resource,
                                   'view': view,
                                   'urls': urls,
                                   'url_rule_options': url_rule_options})
