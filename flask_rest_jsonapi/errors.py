# -*- coding: utf-8 -*-


def jsonapi_errors_serializer(jsonapi_errors):
    return {'errors': [jsonapi_error for jsonapi_error in jsonapi_errors]}
