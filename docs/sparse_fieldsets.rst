.. _sparse_fieldsets:

Sparse fieldsets
================

.. currentmodule:: flask_rest_jsonapi

You can restrict the fields returned by your API using the query string parameter called "fields". It is very useful for performance purposes because fields not returned are not resolved by the API. You can use the "fields" parameter on any kind of route (classical CRUD route or relationships route) and any kind of HTTP methods as long as the method returns data.

.. note::

    Examples are not URL encoded for better readability

The syntax of the fields parameter is ::

    ?fields[<resource_type>]=<list of fields to return>

Example:

.. sourcecode:: http

    GET /persons?fields[person]=display_name HTTP/1.1
    Accept: application/vnd.api+json

In this example person's display_name is the only field returned by the API. No relationship links are returned so the response is very fast because the API doesn't have to do any expensive computation of relationship links.

You can manage returned fields for the entire response even for included objects

Example:

If you don't want to compute relationship links for included computers of a person you can do something like this

.. sourcecode:: http

    GET /persons/1?include=computers&fields[computer]=serial HTTP/1.1
    Accept: application/vnd.api+json

And of course you can combine both like this:

Example:

.. sourcecode:: http

    GET /persons/1?include=computers&fields[computer]=serial&fields[person]=name,computers HTTP/1.1
    Accept: application/vnd.api+json

.. warning::

    If you want to use both "fields" and "include", don't forget to specify the name of the relationship in "fields"; if you don't, the include wont work.
