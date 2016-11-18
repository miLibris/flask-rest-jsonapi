# -*- coding: utf-8 -*-


class HttpException(Exception):

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code


class EntityNotFound(HttpException):

    def __init__(self, entity_name, identifier, additional_message=''):
        super(EntityNotFound, self).__init__(". ".join(["%s with id: %s not found" % (entity_name, identifier),
                                                       additional_message]), 404)
