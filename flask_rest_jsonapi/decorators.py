# -*- coding: utf-8 -*-

from flask import abort, request


def disable_method(f):
    """A decorator to not allow access to a method
    """
    def wrapped_f(*args, **kwargs):
        abort(405)
    return wrapped_f


def check_headers(f):
    """
    """
    def wrapped_f(*args, **kwargs):
        if request.headers['Content-Type'] != 'application/vnd.api+json':
            abort(415)
        if request.headers.get('Accept') and request.headers['Accept'] != 'application/vnd.api+json':
            abort(406)
        return f(*args, **kwargs)
    return wrapped_f


def add_headers(f):
    """
    """
    def wrapped_f(*args, **kwargs):
        response = f(*args, **kwargs)
        response.headers['Content-Type'] = 'application/vnd.api+json'
        return response
    return wrapped_f
