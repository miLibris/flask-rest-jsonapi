# -*- coding: utf-8 -*-

"""Collection of useful http error for the Api"""


class JsonApiException(Exception):
    """Base exception class for unknown errors"""

    title = 'Unknown error'
    status = '500'
    source = None

    def __init__(self, detail, source=None, title=None, status=None, code=None, id_=None, links=None, meta=None):
        """Initialize a jsonapi exception

        :param dict source: the source of the error
        :param str detail: the detail of the error
        """
        self.detail = detail
        self.source = source
        self.code = code
        self.id = id_
        self.links = links or {}
        self.meta = meta or {}
        if title is not None:
            self.title = title
        if status is not None:
            self.status = status

    def to_dict(self):
        """Return values of each fields of an jsonapi error"""
        error_dict = {}
        for field in ('status', 'source', 'title', 'detail', 'id', 'code', 'links', 'meta'):
            if getattr(self, field, None):
                error_dict.update({field: getattr(self, field)})

        return error_dict


class BadRequest(JsonApiException):
    """BadRequest error"""

    title = 'Bad request'
    status = '400'


class InvalidField(BadRequest):
    """Error to warn that a field specified in fields querystring is not in the requested resource schema"""

    title = "Invalid fields querystring parameter."
    source = {'parameter': 'fields'}


class InvalidInclude(BadRequest):
    """Error to warn that a field specified in include querystring parameter is not a relationship of the requested
    resource schema
    """

    title = 'Invalid include querystring parameter.'
    source = {'parameter': 'include'}


class InvalidFilters(BadRequest):
    """Error to warn that a specified filters in querystring parameter contains errors"""

    title = 'Invalid filters querystring parameter.'
    source = {'parameter': 'filters'}


class InvalidSort(BadRequest):
    """Error to warn that a field specified in sort querystring parameter is not in the requested resource schema"""

    title = 'Invalid sort querystring parameter.'
    source = {'parameter': 'sort'}


class ObjectNotFound(JsonApiException):
    """Error to warn that an object is not found in a database"""

    title = 'Object not found'
    status = '404'


class RelatedObjectNotFound(ObjectNotFound):
    """Error to warn that a related object is not found"""

    title = 'Related object not found'


class RelationNotFound(JsonApiException):
    """Error to warn that a relationship is not found on a model"""

    title = 'Relation not found'


class InvalidType(JsonApiException):
    """Error to warn that there is a conflit between resource types"""

    title = 'Invalid type'
    status = '409'


class AccessDenied(JsonApiException):
    """Throw this error when requested resource owner doesn't match the user of the ticket"""

    title = 'Access denied'
    status = '403'
