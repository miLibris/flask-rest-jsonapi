.. _sparse_fieldsets:

Sparse fieldsets
================

.. currentmodule:: flask_rest_jsonapi

You can restrict the fields returned by api with the querystring parameter called "fields". It is very useful for performance purpose because fields not returned are not resolved by api. You can use "fields" parameter on any kind of route (classical CRUD route or relationships route) and any kind of http methods as long as method return data.

.. note::

    Examples are not urlencoded for a better readability

The syntax of a fields is like that ::

    ?fields[<resource_type>]=<list of fields to return>

Example:

.. sourcecode:: http

    GET /persons?fields[person]=display_name HTTP/1.1
    Accept: application/vnd.api+json

In this example person's display_name is the only field returned by the api. No relationships links are returned so the response is very fast because api doesn't have to compute relationships link and it is a very costly work.

You can manage returned fields for the entire response even for included objects

Example:

If you don't want to compute relationships links for included computers of a person you can do something like that

.. sourcecode:: http

    GET /persons/1?include=computers&fields[computer]=serial HTTP/1.1
    Accept: application/vnd.api+json

And of course you can combine both like that:

Example:

.. sourcecode:: http

    GET /persons/1?include=computers&fields[computer]=serial&fields[person]=name,computers HTTP/1.1
    Accept: application/vnd.api+json

.. warning::

    If you want to use both "fields" and "include" don't forget to specify the name of the relationship in fields; if you don't the include wont work.
