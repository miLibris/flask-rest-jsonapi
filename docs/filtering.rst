.. _filtering:

Filtering
=========

.. currentmodule:: flask_rest_jsonapi

Flask-REST-JSONAPI as a very flexible filtering system. The filtering system is completely related to the data layer used by the ResourceList manager. I will explain the filtering interface for SQLAlchemy data layer but you can use the same interface to your filtering implementation of your custom data layer. The only requirement is that you have to use the "filter" querystring parameter to make filtering according to the JSONAPI 1.0 specification.

.. note::

    Examples are not urlencoded for a better readability

SQLAlchemy
----------

The filtering system of SQLAlchemy data layer has exactly the same interface as the filtering system of `Flask-Restless <https://flask-restless.readthedocs.io/en/stable/searchformat.html#query-format>`_.
So this is a first example:

.. sourcecode:: http

    GET /persons?filter=[{"name":"name","op":"eq","val":"John"}] HTTP/1.1
    Accept: application/vnd.api+json

In this example we want to retrieve persons which name is John. So we can see that the filtering interface completely fit the filtering interface of SQLAlchemy: a list a filter information.

    :name: the name of the field you want to filter on
    :op: the operation you want to use (all sqlalchemy operations are available)
    :val: the value that you want to compare. You can replace this by "field" if you want to compare against the value of an other field

Example with field:

.. sourcecode:: http

    GET /persons?filter=[{"name":"name","op":"eq","field":"birth_date"}] HTTP/1.1
    Accept: application/vnd.api+json

In this example, we want to retrieve persons that name is equal to his birth_date. I know, this example is absurd but it is just to explain the syntax of this kind of filter.

If you want to filter through relationships you can do that:

.. sourcecode:: http

    GET /persons?filter=[
      {
        "name": "computers",
        "op": "any",
        "val": {
          "name": "serial",
          "op": "ilike",
          "val": "%Amstrad%"
        }
      }
    ] HTTP/1.1
    Accept: application/vnd.api+json

.. note ::

    When you filter on relationships use "any" operator for "to many" relationships and "has" operator for "to one" relationships.

There is a shortcut to achieve the same filter:

.. sourcecode:: http

    GET /persons?filter=[{"name":"computers__serial","op":"ilike","val":"%Amstrad%"}] HTTP/1.1
    Accept: application/vnd.api+json

You can also use boolean combination of operations:

.. sourcecode:: http

    GET /persons?filter=[
      {
        "name":"computers__serial",
        "op":"ilike",
        "val":"%Amstrad%"
      },
      {
        "or": {
          [
            {
              "not": {
                "name": "name",
                "op": "eq",
                "val":"John"
              }
            },
            {
              "and": [
                {
                  "name": "name",
                  "op": "like",
                  "val": "%Jim%"
                },
                {
                  "name": "birth_date",
                  "op": "gt",
                  "val": "1990-01-01"
                }
              ]
            }
          ]
        }
      }
    ] HTTP/1.1
    Accept: application/vnd.api+json

Common available operators:

* any: used to filter on to many relationships
* between: used to filter a field between two values
* endswith: check if field ends with a string
* eq: check if field is equal to something
* ge: check if field is greater than or equal to something
* gt: check if field is greater than to something
* has: used to filter on to one relationships
* ilike: check if field contains a string (case insensitive)
* in\_: check if field is in a list of values
* is\_: check if field is a value
* isnot: check if field is not a value
* like: check if field contains a string
* le: check if field is less than or equal to something
* lt: check if field is less than to something
* match: check if field match against a string or pattern
* ne: check if field is not equal to something
* notilike: check if field does not contains a string (case insensitive)
* notin\_: check if field is not in a list of values
* notlike: check if field does not contains a string
* startswith: check if field starts with a string

.. note::

    Availables operators depend on field type in your model

Simple filters
--------------

Simple filter adds support for a simplified form of filters and supports only *eq* operator.
Each simple filter transforms to original filter and appends to list of filters.

For example

.. sourcecode:: http

    GET /persons?filter[name]=John HTTP/1.1
    Accept: application/vnd.api+json

equals to:

.. sourcecode:: http

    GET /persons?filter[name]=[{"name":"name","op":"eq","val":"John"}] HTTP/1.1
    Accept: application/vnd.api+json


You can also use more than one simple filter in request:

.. sourcecode:: http

    GET /persons?filter[name]=John&filter[gender]=male HTTP/1.1
    Accept: application/vnd.api+json

which equals to:

.. sourcecode:: http

    GET /persons?filter[name]=[{"name":"name","op":"eq","val":"John"}, {"name":"gender","op":"eq","val":"male"}] HTTP/1.1
