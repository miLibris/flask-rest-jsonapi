# -*- coding: utf-8 -*-


class ErrorFormatter(object):

    @staticmethod
    def format_error(messages):
        return {'errors': [{'detail': message} for message in messages]}
