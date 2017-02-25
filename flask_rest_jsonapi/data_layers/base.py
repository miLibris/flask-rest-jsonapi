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
