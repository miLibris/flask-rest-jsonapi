# -*- coding: utf-8 -*-


class BaseDataLayer(object):

    def __init__(self, *args, **kwargs):
        """Intialize an data layer instance with kwargs

        :param dict kwargs: information about data layer instance
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def create_object(self, data, opts, **view_kwargs):
        """Create an object

        :param dict data: the data validated by marshmallow
        :param opts: meta options from the resource class
        :param dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object
        """
        raise NotImplemented

    def get_object(self, **view_kwargs):
        """Retrieve an object

        :params dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object
        """
        raise NotImplemented

    def get_collection(self, qs, **view_kwargs):
        """Retrieve a collection of objects

        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the number of object and the list of objects
        """
        raise NotImplemented

    def update_object(self, obj, data, opts, **view_kwargs):
        """Update an object

        :param DeclarativeMeta obj: an object
        :param dict data: the data validated by marshmallow
        :param opts: meta options from the resource class
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if object have changed else False
        """
        raise NotImplemented

    def delete_object(self, *args, **kwargs):
        """Delete an item through the data layer
        """
        raise NotImplemented

    def create_relationship(self, *args, **kwargs):
        """Create a relationship
        """
        raise NotImplemented

    def get_relationship(self, *args, **kwargs):
        """Get information about a relationship
        """
        raise NotImplemented

    def update_relationship(self, *args, **kwargs):
        """Update a relationship
        """
        raise NotImplemented

    def delete_relationship(self, *args, **kwargs):
        """Delete a relationship
        """
        raise NotImplemented

    def configure(self, meta):
        """Rewrite default implemantation of methods or attributs

        :param class meta: information from Meta class used to configure the data layer instance
        """
        raise NotImplemented
