# -*- coding: utf-8 -*-


class RelationNotFound(Exception):
    pass


class InvalidField(Exception):

    message = "Invalid fields querystring parameter."

    def __init__(self, message):
        self.message = " ".join([self.message, message])


class InvalidInclude(Exception):

    message = "Invalid include querystring parameter."

    def __init__(self, message):
        self.message = " ".join([self.message, message])


class HttpException(Exception):

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code


class EntityNotFound(HttpException):

    def __init__(self, entity_name, identifier, additional_message=''):
        super(EntityNotFound, self).__init__(". ".join(["%s with id: %s not found" % (entity_name, identifier),
                                                       additional_message]), 404)


class RelatedItemNotFound(HttpException):

    message = "Related item with id %s not found"

    def __init__(self, related_item_id):
        message = self.message % related_item_id
        super(RelatedItemNotFound, self).__init__(message, 404)
