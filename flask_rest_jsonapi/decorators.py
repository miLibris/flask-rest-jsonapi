# -*- coding: utf-8 -*-

import json

from flask import request, make_response

from flask_rest_jsonapi.exceptions import JsonApiException


def not_allowed_method(f):
    """A decorator to disallow method access

    :param callable f: the function to decorate
    :return callable: the wrapped function
    """
    def wrapped_f(*args, **kwargs):
        raise JsonApiException('', "Acces to this method have been disallowed", title="MethodNotAllowed", status=405)
    return wrapped_f


def check_headers(f):
    """Check headers according to jsonapi reference

    :param callable f: the function to decorate
    :return callable: the wrapped function
    """
    def wrapped_f(*args, **kwargs):
        if request.headers['Content-Type'] != 'application/vnd.api+json':
            error = json.dumps({'jsonapi': {'version': '1.0'},
                                'errors': [{'source': '',
                                            'detail': "Content-Type header must be application/vnd.api+json",
                                            'title': 'InvalidContentTypeHeader',
                                            'status': 415}]})
            return make_response(error, 415, {'Content-Type': 'application/vnd.api+json'})
        if request.headers.get('Accept') and request.headers['Accept'] != 'application/vnd.api+json':
            error = json.dumps({'jsonapi': {'version': '1.0'},
                                'errors': [{'source': '',
                                            'detail': "Accept header must be application/vnd.api+json",
                                            'title': 'InvalidAcceptHeader',
                                            'status': 406}]})
            return make_response(error, 406, {'Content-Type': 'application/vnd.api+json'})
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
        error_message = "You must provide {error_field} in {cls} to get access to the default {method} method"
        error_data = {'cls': cls.__name__, 'method': method_name}

        if not hasattr(self, 'data_layer'):
            error_data.update({'error_field': 'a data layer class'})
            raise Exception(error_message.format(**error_data))

        if method_name != 'delete':
            if not hasattr(self, 'schema'):
                error_data.update({'error_field': 'a schema class'})
                raise Exception(error_message.format(**error_data))

        return f(self, *args, **kwargs)

    return wrapped_f
