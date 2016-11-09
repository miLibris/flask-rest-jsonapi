# -*- coding: utf-8 -*-


class BaseDataLayer(object):

    def get_item(self, *args, **kwargs):
        """Get an item through the data layer
        """
        raise NotImplemented

    def persiste_update(self, *args, **kwargs):
        """Make changes made on an item persistant through the data layer
        """
        raise NotImplemented

    def get_items(self, *args, **kwargs):
        """Get a collection of items through the data layer
        """
        raise NotImplemented

    def create_and_save_item(self, *args, **kwargs):
        """Create an instance of the item and store it through the data layer
        """
        raise NotImplemented

    def configure(self, *args, **kwargs):
        """Make change on the class instance. For example: add new methods to the data layer instance class.
        """
        pass
