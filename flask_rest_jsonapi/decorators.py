# -*- coding: utf-8 -*-

import json

from flask import request, make_response

from flask_rest_jsonapi.errors import jsonapi_errors


def check_headers(f):
    """Check headers according to jsonapi reference

    :param callable f: the function to decorate
    :return callable: the wrapped function
    """
    def wrapped_f(*args, **kwargs):
        if request.method in ('POST', 'PATCH'):
            if request.headers['Content-Type'] != 'application/vnd.api+json':
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
        return f(*args, **kwargs)
    return wrapped_f


def check_method_requirements(f):
    """Check methods requirements

    :param callable f: the function to decorate
    :return callable: the wrapped function
    """
    def wrapped_f(self, *args, **kwargs):
        cls = type(self)
        error_message = "You must provide {error_field} in {cls} to get access to the default {method} method"
        error_data = {'cls': cls.__name__, 'method': request.method}

        if not hasattr(self, '_data_layer'):
            error_data.update({'error_field': 'a data layer class'})
            raise Exception(error_message.format(**error_data))

        if request.method != 'DELETE':
            if not hasattr(self, 'schema'):
                error_data.update({'error_field': 'a schema class'})
                raise Exception(error_message.format(**error_data))

        return f(self, *args, **kwargs)

    return wrapped_f
