# -*- coding: utf-8 -*-

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
    def wrapped_f(self, *args, **kwargs):
        cls_name = type(self).__name__
        method_name = f.__name__.upper()

        error_message = "You must provide %(error_field)s in %(cls)s to get access to the default %(method)s method"
        error_message_data = {'cls': cls_name, 'method': method_name}

        if not hasattr(self, 'data_layer'):
            raise Exception(error_message % error_message_data.update({'error_field': 'data layer information'}))

        if 'ResourceList' in [cls_name for cls_ in type(self).__bases__]:
            if not hasattr(self, 'schema') or not isinstance(self.schema, dict) \
                    or self.schema.get('cls') is None:
                raise Exception(error_message % error_message_data.update({'error_field': 'schema information'}))
            if method_name == 'GET':
                if not hasattr(self, 'resource_type'):
                    raise Exception(error_message % error_message_data.update({'error_field': 'resource_type'}))
                if not hasattr(self, 'endpoint') or not isinstance(self.endpoint, dict) \
                        or self.endpoint.get('name') is None:
                    raise Exception(error_message % error_message_data.update({'error_field': 'endpoint infromation'}))

        if 'ResourceDetail' in [cls_name for cls_ in type(self).__bases__]:
            if method_name in ('GET', 'PATCH'):
                if not hasattr(self, 'schema') or not isinstance(self.schema, dict) \
                        or self.schema.get('cls') is None:
                    raise Exception(error_message % error_message_data.update({'error_field': 'schema information'}))
                if method_name == 'GET':
                    if not hasattr(self, 'resource_type'):
                        raise Exception(error_message % error_message_data.update({'error_field': 'resource_type'}))

        if 'ResourceRelationship' in [cls_name for cls_ in type(self).__bases__]:
            if method_name in ('GET', 'POST', 'PATCH', 'DELETE'):
                if not hasattr(self, 'related_resource_type'):
                    raise Exception(error_message % error_message_data.update({'error_field': 'related_resource_type'}))
                if not hasattr(self, 'related_id_field'):
                    raise Exception(error_message % error_message_data.update({'error_field': 'related_id_field'}))
                if method_name == 'GET':
                    if not hasattr(self, 'endpoint'):
                        raise Exception(error_message % error_message_data.update({'error_field': 'endpoint'}))
                    if not hasattr(self, 'related_endpoint'):
                        raise Exception(error_message % error_message_data.update({'error_field': 'related_endpoint'}))

        return f(self, *args, **kwargs)

    return wrapped_f
