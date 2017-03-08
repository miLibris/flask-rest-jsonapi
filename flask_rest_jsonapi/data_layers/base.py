# -*- coding: utf-8 -*-


class BaseDataLayer(object):

    def __init__(self, *args, **kwargs):
        """Intialize an data layer instance with kwargs

        :param dict kwargs: information about data layer instance
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def create_object(self, data, **view_kwargs):
        """Create an object

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object
        """
        raise NotImplementedError

    def get_object(self, **view_kwargs):
        """Retrieve an object

        :params dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object
        """
        raise NotImplementedError

    def get_collection(self, qs, **view_kwargs):
        """Retrieve a collection of objects

        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the number of object and the list of objects
        """
        raise NotImplementedError

    def update_object(self, obj, data, **view_kwargs):
        """Update an object

        :param DeclarativeMeta obj: an object
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if object have changed else False
        """
        raise NotImplementedError

    def delete_object(self, obj, **view_kwargs):
        """Delete an item through the data layer

        :param DeclarativeMeta obj: an object
        :param dict view_kwargs: kwargs from the resource view
        """
        raise NotImplementedError

    def create_relationship(self, json_data, relationship_field, related_id_field, **view_kwargs):
        """Create a relationship

        :param dict json_data: the request params
        :param str relationship_field: the model attribut used for relationship
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return boolean: True if relationship have changed else False
        """
        raise NotImplementedError

    def get_relationship(self, relationship_field, related_type_, related_id_field, **view_kwargs):
        """Get information about a relationship

        :param str relationship_field: the model attribut used for relationship
        :param str related_type_: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        raise NotImplementedError

    def update_relationship(self, *args, **kwargs):
        """Update a relationship
        """
        raise NotImplementedError

    def delete_relationship(self, *args, **kwargs):
        """Delete a relationship
        """
        raise NotImplementedError

    def configure(self, meta):
        """Rewrite default implemantation of methods or attributs

        :param class meta: information from Meta class used to configure the data layer instance
        """
        raise NotImplementedError
