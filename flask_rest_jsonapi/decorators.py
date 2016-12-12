# -*- coding: utf-8 -*-

from flask import abort, request


def disable_method(f):
    """A decorator disallow method access
    """
    def wrapped_f(*args, **kwargs):
        abort(405)
    return wrapped_f


def check_headers(f):
    """Check headers according to jsonapi reference
    """
    def wrapped_f(*args, **kwargs):
        if request.headers['Content-Type'] != 'application/vnd.api+json':
            abort(415)
        if request.headers.get('Accept') and request.headers['Accept'] != 'application/vnd.api+json':
            abort(406)
        return f(*args, **kwargs)
    return wrapped_f


def add_headers(f):
    """Add headers according to jsonapi reference
    """
    def wrapped_f(*args, **kwargs):
        response = f(*args, **kwargs)
        response.headers['Content-Type'] = 'application/vnd.api+json'
        return response
    return wrapped_f


def check_requirements(f):
    """
    """
    def wrapped_f(self, *args, **kwargs):
        cls = type(self)
        if not hasattr(self, 'data_layer'):
            raise Exception("You must provide data layer information in %s to get access to the default %s \
                            method" % (cls.__name__, f.__name__.upper()))
        if 'ResourceList' in [cls_.__name__ for cls_ in cls.__bases__]:
            if not hasattr(self, 'schema') or not isinstance(self.schema, dict) \
                    or self.schema.get('cls') is None:
                raise Exception("You must provide schema information in %s to get access to the default %s method"
                                % (cls.__name__, f.__name__.upper()))
            if f.__name__.upper() == 'GET':
                if not hasattr(self, 'resource_type'):
                    raise Exception("You must provide resource type in %s to get access to the default %s method"
                                    % (cls.__name__, f.__name__.upper()))
                if not hasattr(self, 'endpoint') or not isinstance(self.endpoint, dict) \
                        or self.endpoint.get('name') is None:
                    raise Exception("You must provide schema information in %s to get access to the default %s method"
                                    % (cls.__name__, f.__name__.upper()))
        if 'ResourceDetail' in [cls_.__name__ for cls_ in cls.__bases__]:
            if f.__name__.upper() in ('GET', 'PATCH'):
                if not hasattr(self, 'schema') or not isinstance(self.schema, dict) \
                        or self.schema.get('cls') is None:
                    raise Exception("You must provide schema information in %s to get access to the default %s method"
                                    % (cls.__name__, f.__name__.upper()))
                if f.__name__.upper() == 'GET':
                    if not hasattr(self, 'resource_type'):
                        raise Exception("You must provide resource type in %s to get access to the default %s method"
                                        % (cls.__name__, f.__name__.upper()))

        return f(self, *args, **kwargs)
    return wrapped_f
