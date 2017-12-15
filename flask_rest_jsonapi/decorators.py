# -*- coding: utf-8 -*-

"""Decorators to check headers and method requirements for each Api calls"""

from functools import wraps

from flask import request, make_response, jsonify

from flask_rest_jsonapi.errors import jsonapi_errors


def check_headers(func):
    """Check headers according to jsonapi reference

    :param callable func: the function to decorate
    :return callable: the wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method in ('POST', 'PATCH'):
            if 'Content-Type' in request.headers and\
                    'application/vnd.api+json' in request.headers['Content-Type'] and\
                    request.headers['Content-Type'] != 'application/vnd.api+json':
                error = jsonify(jsonapi_errors([{'source': '',
                                                 'detail': "Content-Type header must be application/vnd.api+json",
                                                 'title': 'Invalid request header',
                                                 'status': '415'}]))
                return make_response(error, 415, {'Content-Type': 'application/vnd.api+json'})
        if 'Accept' in request.headers:
            flag = False
            for accept in request.headers['Accept'].split(','):
                if accept.strip() == 'application/vnd.api+json':
                    flag = False
                    break
                if 'application/vnd.api+json' in accept and accept.strip() != 'application/vnd.api+json':
                    flag = True
            if flag is True:
                error = jsonify(jsonapi_errors([{'source': '',
                                                 'detail': ('Accept header must be application/vnd.api+json without'
                                                            'media type parameters'),
                                                 'title': 'Invalid request header',
                                                 'status': '406'}]))
                return make_response(error, 406, {'Content-Type': 'application/vnd.api+json'})
        return func(*args, **kwargs)
    return wrapper


def check_method_requirements(func):
    """Check methods requirements

    :param callable func: the function to decorate
    :return callable: the wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        error_message = "You must provide {error_field} in {cls} to get access to the default {method} method"
        error_data = {'cls': args[0].__class__.__name__, 'method': request.method.lower()}

        if not hasattr(args[0], '_data_layer'):
            error_data.update({'error_field': 'a data layer class'})
            raise Exception(error_message.format(**error_data))

        if request.method != 'DELETE':
            if not hasattr(args[0], 'schema'):
                error_data.update({'error_field': 'a schema class'})
                raise Exception(error_message.format(**error_data))

        return func(*args, **kwargs)
    return wrapper
