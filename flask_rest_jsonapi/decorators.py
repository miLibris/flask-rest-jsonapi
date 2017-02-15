# -*- coding: utf-8 -*-

from flask import abort, request


def not_allowed_method(f):
    """A decorator to disallow method access

    :param callable f: the function to decorate
    :return callable: the wrapped function
    """
    def wrapped_f(*args, **kwargs):
        abort(405)
    return wrapped_f


def check_headers(f):
    """Check headers according to jsonapi reference

    :param callable f: the function to decorate
    :return callable: the wrapped function
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

    :param callable f: the function to decorate
    :return callable: the wrapped function
    """
    def wrapped_f(*args, **kwargs):
        response = f(*args, **kwargs)
        response.headers['Content-Type'] = 'application/vnd.api+json'
        return response
    return wrapped_f


def check_method_requirements(f):
    """Check methods requirements

    :param callable f: the function to decorate
    :return callable: the wrapped function
    """
    def wrapped_f(self, *args, **kwargs):
        cls = type(self)
        cls_bases = [cls_.__name__ for cls_ in cls.__bases__]
        method_name = f.__name__
        error_message = "You must provide %(error_field)s in %(cls)s to get access to the default %(method)s method"
        error_data = {'cls': cls.__name__, 'method': method_name}

        if not hasattr(self, 'data_layer'):
            error_data.update({'error_field': 'data layer information'})
            raise Exception(error_message % error_data)

        if not hasattr(self, 'schema'):
            error_data.update({'error_field': 'schema information'})
            raise Exception(error_message % error_data)

        if 'ResourceRelationship' in cls_bases:
            if not hasattr(self, 'related_type_'):
                error_data.update({'error_field': 'related_type_'})
                raise Exception(error_message % error_data)
            if method_name == 'get':
                if not hasattr(self, 'related_endpoint'):
                    error_data.update({'error_field': 'related_endpoint'})
                    raise Exception(error_message % error_data)

        return f(self, *args, **kwargs)

    return wrapped_f
