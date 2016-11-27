# -*- coding: utf-8 -*-

import inspect

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
    def wrapped_f(*args, **kwargs):
        cls = get_class_from_function(f)
        if not hasattr(args[0], 'data_layer'):
            raise Exception("You must provide data layer information in %s to get access to the default %s \
                            method" % (get_class_from_function(f).__name__, f.__name__.upper()))
        if 'ResourceList' in [cls_.__name__ for cls_ in cls.__bases__]:
            if not hasattr(args[0], 'schema') or not isinstance(args[0].schema, dict) \
                    or args[0].schema.get('cls') is None:
                raise Exception("You must provide schema information in %s to get access to the default %s method"
                                % (get_class_from_function(f).__name__, f.__name__.upper()))
            if f.__name__.upper() == 'GET':
                if not hasattr(args[0], 'resource_type'):
                    raise Exception("You must provide resource type in %s to get access to the default %s method"
                                    % (get_class_from_function(f).__name__, f.__name__.upper()))
                if not hasattr(args[0], 'endpoint') or not isinstance(args[0].endpoint, dict) \
                        or args[0].endpoint.get('alias') is None:
                    raise Exception("You must provide schema information in %s to get access to the default %s method"
                                    % (get_class_from_function(f).__name__, f.__name__.upper()))
        if 'ResourceDetail' in [cls_.__name__ for cls_ in cls.__bases__]:
            if f.__name__.upper() in ('GET', 'PATCH'):
                if not hasattr(args[0], 'schema') or not isinstance(args[0].schema, dict) \
                        or args[0].schema.get('cls') is None:
                    raise Exception("You must provide schema information in %s to get access to the default %s method"
                                    % (get_class_from_function(f).__name__, f.__name__.upper()))
                if f.__name__.upper() == 'GET':
                    if not hasattr(args[0], 'resource_type'):
                        raise Exception("You must provide resource type in %s to get access to the default %s method"
                                        % (get_class_from_function(f).__name__, f.__name__.upper()))

        return f(*args, **kwargs)
    return wrapped_f


# Utils function
def get_class_from_function(f):
    if inspect.isfunction(f):
            cls = getattr(inspect.getmodule(f),
                          f.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
            if isinstance(cls, type):
                return cls
