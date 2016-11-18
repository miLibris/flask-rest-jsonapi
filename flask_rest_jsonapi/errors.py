# -*- coding: utf-8 -*-


class ErrorFormatter(object):

    @staticmethod
    def format_error(messages):
        """Create error response structure according to jsonapi reference

        :param list messages: a list of string of errors
        :return dict: errors according to jsonapi reference
        """
        return {'errors': [{'detail': message} for message in messages]}
