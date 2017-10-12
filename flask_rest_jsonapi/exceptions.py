# -*- coding: utf-8 -*-

"""Collection of useful http error for the Api"""


class JsonApiException(Exception):
    """Base exception class for unknown errors"""

    title = 'Unknown error'
    status = 500

    def __init__(self, source, detail, title=None, status=None):
        """Initialize a jsonapi exception

        :param dict source: the source of the error
        :param str detail: the detail of the error
        """
        self.source = source
        self.detail = detail
        if title is not None:
            self.title = title
        if status is not None:
            self.status = status

    def to_dict(self):
        """Return values of each fields of an jsonapi error"""
        return {'status': self.status,
                'source': self.source,
                'title': self.title,
                'detail': self.detail}


class BadRequest(JsonApiException):
    """BadRequest error"""

    title = "Bad request"
    status = 400


class InvalidField(BadRequest):
    """Error to warn that a field specified in fields querystring is not in the requested resource schema"""

    title = "Invalid fields querystring parameter."

    def __init__(self, detail):
        """Initialize InvalidField error instance

        :param str detail: the detail of the error
        """
        self.source = {'parameter': 'fields'}
        self.detail = detail


class InvalidInclude(BadRequest):
    """Error to warn that a field specified in include querystring parameter is not a relationship of the requested
    resource schema
    """

    title = "Invalid include querystring parameter."

    def __init__(self, detail):
        """Initialize InvalidInclude error instance

        :param str detail: the detail of the error
        """
        self.source = {'parameter': 'include'}
        self.detail = detail


class InvalidFilters(BadRequest):
    """Error to warn that a specified filters in querystring parameter contains errors"""

    title = "Invalid filters querystring parameter."

    def __init__(self, detail):
        """Initialize InvalidField error instance

        :param str detail: the detail of the error
        """
        self.source = {'parameter': 'filters'}
        self.detail = detail


class InvalidSort(BadRequest):
    """Error to warn that a field specified in sort querystring parameter is not in the requested resource schema"""

    title = "Invalid sort querystring parameter."

    def __init__(self, detail):
        """Initialize InvalidField error instance

        :param str detail: the detail of the error
        """
        self.source = {'parameter': 'sort'}
        self.detail = detail


class ObjectNotFound(JsonApiException):
    """Error to warn that an object is not found in a database"""

    title = "Object not found"
    status = 404


class RelatedObjectNotFound(ObjectNotFound):
    """Error to warn that a related object is not found"""

    title = "Related object not found"


class RelationNotFound(JsonApiException):
    """Error to warn that a relationship is not found on a model"""

    title = "Relation not found"


class InvalidType(JsonApiException):
    """Error to warn that there is a conflit between resource types"""

    title = "Invalid type"
    status = 409
