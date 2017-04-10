# -*- coding: utf-8 -*-

import json
from functools import wraps

from flask import request, make_response

from flask_rest_jsonapi.errors import jsonapi_errors


def check_headers(func):
    """Check headers according to jsonapi reference

    :param callable func: the function to decorate
    :return callable: the wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method in ('POST', 'PATCH'):
            if 'Content-Type' not in request.headers or request.headers['Content-Type'] != 'application/vnd.api+json':
                error = json.dumps(jsonapi_errors([{'source': '',
                                                    'detail': "Content-Type header must be application/vnd.api+json",
                                                    'title': 'InvalidRequestHeader',
                                                    'status': 415}]))
                return make_response(error, 415, {'Content-Type': 'application/vnd.api+json'})
        if request.headers.get('Accept') and request.headers['Accept'] != 'application/vnd.api+json':
            error = json.dumps(jsonapi_errors([{'source': '',
                                                'detail': "Accept header must be application/vnd.api+json",
                                                'title': 'InvalidRequestHeader',
                                                'status': 406}]))
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
