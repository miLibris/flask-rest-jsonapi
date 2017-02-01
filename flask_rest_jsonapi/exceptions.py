# -*- coding: utf-8 -*-


class JsonApiException(Exception):

    title = 'Unknow error'
    status = 500

    def __init__(self, source, detail):
        self.source = source
        self.detail = detail

    def to_dict(self):
        return {'status': self.status,
                'source': {'pointer': self.source},
                'title': self.title,
                'detail': self.detail}


class BadRequest(JsonApiException):
    title = "Bad request"
    status = 400


class InvalidField(BadRequest):
    title = "Invalid fields querystring parameter."


class InvalidInclude(BadRequest):
    title = "Invalid include querystring parameter."


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
