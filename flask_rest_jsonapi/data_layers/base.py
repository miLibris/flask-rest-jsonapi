# -*- coding: utf-8 -*-


class BaseDataLayer(object):

    def __init__(self, *args, **kwargs):
        """Intialize an data layer instance with kwargs

        :param dict kwargs: information about data layer instance
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def create_object(self, *args, **kwargs):
        """Create an instance of an object and store it through the data layer
        """
        raise NotImplemented

    def get_object(self, *args, **kwargs):
        """Get an object through the data layer
        """
        raise NotImplemented

    def get_collection(self, *args, **kwargs):
        """Get a collection of objects through the data layer
        """
        raise NotImplemented

    def update_object(self, *args, **kwargs):
        """Update an instance of an object and store changes through the data layer
        """
        raise NotImplemented

    def delete_object(self, *args, **kwargs):
        """Delete an item through the data layer
        """
        raise NotImplemented

    def before_create_object(self, data, **view_kwargs):
        """Provide additional data before instance creation

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        raise NotImplemented

    def before_update_object(self, obj, data, **view_kwargs):
        """Make checks or provide additional data before update instance

        :param obj: an object from data layer
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        raise NotImplemented

    def before_delete_object(self, obj, **view_kwargs):
        """Make checks before delete instance

        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        raise NotImplemented

    def configure(self, *args, **kwargs):
        """Make change on the class instance. For example: add new methods to the data layer instance class.
        """
        pass
