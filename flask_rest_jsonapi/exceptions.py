# -*- coding: utf-8 -*-


class JsonApiException(Exception):

    title = 'Unknow error'
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
        return {'status': self.status,
                'source': self.source,
                'title': self.title,
                'detail': self.detail}


class BadRequest(JsonApiException):
    title = "Bad request"
    status = 400


class InvalidField(BadRequest):
    title = "Invalid fields querystring parameter."

    def __init__(self, detail):
        self.source = {'parameter': 'fields'}
        self.detail = detail


class InvalidInclude(BadRequest):
    title = "Invalid include querystring parameter."

    def __init__(self, detail):
        self.source = {'parameter': 'include'}
        self.detail = detail


class InvalidFilters(BadRequest):
    title = "Invalid filters querystring parameter."

    def __init__(self, detail):
        self.source = {'parameter': 'filters'}
        self.detail = detail


class InvalidSort(BadRequest):
    title = "Invalid sort querystring parameter."

    def __init__(self, detail):
        self.source = {'parameter': 'sort'}
        self.detail = detail


class ObjectNotFound(JsonApiException):
    title = "Object not found"
    status = 404


class RelatedObjectNotFound(ObjectNotFound):
    title = "Related object not found"


class RelationNotFound(JsonApiException):
    title = "Relation not found"


class InvalidType(JsonApiException):
    title = "Invalid type"
    status = 409
