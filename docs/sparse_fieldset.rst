.. _sparse_fieldset:

Sparse fieldset
===============

.. currentmodule:: flask_rest_jsonapi

You can restrict the fields returned by api with the querystring parameter called fields. It is very useful for performance purpose because fields not returned are not resolved by api. You can use "fields" parameter on any kind of url (classical CRUD url or relationships url) and any kind of http methods as long as method return data.

.. note::

    Urls examples are not urlencoded for a better readability

The syntax of a fields is like that ::

    ?fields[<resource_type>]=<list of fields to return>

Example

.. sourcecode:: http

    GET /persons?fields[person]=name HTTP/1.1
    Accept: application/vnd.api+json

You can manage returned fields for the entire response even for included objects

Example

If you don't want to compute relationships links for included computers of a person you can do something like that

.. sourcecode:: http

    GET /persons/1?include=computers&fields[computer]=serial HTTP/1.1
    Accept: application/vnd.api+json

And of course you can combine both

Example

.. sourcecode:: http

    GET /persons/1?include=computers&fields[computer]=serial&fields[person]=name,computers HTTP/1.1
    Accept: application/vnd.api+json

.. warning::

    If you want to use both fields and include for a resource_type don't forget to specify the name of the relation in fields; if you don't the include wont work.
