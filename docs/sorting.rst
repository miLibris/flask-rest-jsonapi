.. _sorting:

Sorting
=======

.. currentmodule:: flask_rest_jsonapi

You can sort results with querystring parameter named "sort"

.. note::

    Examples are not urlencoded for a better readability

Example:

.. sourcecode:: http

    GET /persons?sort=name HTTP/1.1
    Accept: application/vnd.api+json

Multiple sort
-------------

You can sort on multiple fields like that:

.. sourcecode:: http

    GET /persons?sort=name,birth_date HTTP/1.1
    Accept: application/vnd.api+json

Descending sort
---------------

You can make desc sort with the character "-" like that:

.. sourcecode:: http

    GET /persons?sort=-name HTTP/1.1
    Accept: application/vnd.api+json

Multiple sort + Descending sort
-------------------------------

Of course, you can combine both like that:

.. sourcecode:: http

    GET /persons?sort=-name,birth_date HTTP/1.1
    Accept: application/vnd.api+json
