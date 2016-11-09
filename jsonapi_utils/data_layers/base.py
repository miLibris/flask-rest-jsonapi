# -*- coding: utf-8 -*-


class BaseDataLayer(object):

    def get_item(self, *args, **kwargs):
        """
        """
        raise NotImplemented

    def persiste_update(self, *args, **kwargs):
        """
        """
        raise NotImplemented

    def get_items(self, *args, **kwargs):
        """
        """
        raise NotImplemented

    def create_and_save_item(self, *args, **kwargs):
        """
        """
        raise NotImplemented

    def add_list_methods(self, *args, **kwargs):
        """
        """
        pass
