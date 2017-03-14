.. _pagination:

Pagination
==========

.. currentmodule:: flask_rest_jsonapi

When you use the default implementation of get method on a ResourceList your results will be paginated by default. Default pagination size is 20 but you can manage it from querystring with the url parameter called page.

.. note::

    Urls examples are not urlencoded for a better readability

Size
----

You can control the page size like that:

.. sourcecode:: http

    GET /persons?page[size]=10 HTTP/1.1
    Accept: application/vnd.api+json

Number
------

You can control the page number like that:

.. sourcecode:: http

    GET /persons?page[size]=10&page[number]=2 HTTP/1.1
    Accept: application/vnd.api+json

Disable pagination
------------------

You can disable pagination with size = 0

.. sourcecode:: http

    GET /persons?page[size]=0 HTTP/1.1
    Accept: application/vnd.api+json
