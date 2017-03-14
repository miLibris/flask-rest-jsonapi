.. _sorting:

Sorting
=======

.. currentmodule:: flask_rest_jsonapi

You can sort result with querystring parameter called sort

.. note::

    Urls examples are not urlencoded for a better readability

Example

.. sourcecode:: http

    GET /persons?sort=name HTTP/1.1
    Accept: application/vnd.api+json

Muliple sort
------------

You can sort on multiple fields like that

.. sourcecode:: http

    GET /persons?sort=name,birth_date HTTP/1.1
    Accept: application/vnd.api+json

Descendant sort
---------------

You can make desc sort with the character "-" like that

.. sourcecode:: http

    GET /persons?sort=-name,birth_date HTTP/1.1
    Accept: application/vnd.api+json
