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
        method_name = f.__name__
        error_message = "You must provide %(error_field)s in %(cls)s to get access to the default %(method)s method"
        error_data = {'cls': cls.__name__, 'method': method_name}

        if not hasattr(self, 'data_layer'):
            error_data.update({'error_field': 'a data layer class'})
            raise Exception(error_message % error_data)

        if method_name != 'delete':
            if not hasattr(self, 'schema'):
                error_data.update({'error_field': 'a schema class'})
                raise Exception(error_message % error_data)

            if not hasattr(self, 'opts'):
                error_data.update({'error_field': 'a opts class'})
                raise Exception(error_message % error_data)

        return f(self, *args, **kwargs)

    return wrapped_f
