# -*- coding: utf-8 -*-

from flask import abort


def disable_method(f):
    """A decorator to not allow access to a method
    """
    def wrapped_f(*args, **kwargs):
        abort(405)
    return wrapped_f
