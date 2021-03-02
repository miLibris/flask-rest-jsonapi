.. _filtering:

Filtering
=========

.. currentmodule:: flask_rest_jsonapi

Flask-REST-JSONAPI has a very flexible filtering system. The filtering system is directly attached to the data layer used by the ResourceList manager. These examples show the filtering interface for SQLAlchemy's data layer but you can use the same interface for your custom data layer's filtering implementation as well. The only requirement is that you have to use the "filter" query string parameter to filter according to the JSON:API 1.0 specification.

.. note::

    Examples are not urlencoded for a better readability

SQLAlchemy
----------

The filtering system of SQLAlchemy's data layer has exactly the same interface as the one used in `Flask-Restless <https://flask-restless.readthedocs.io/en/stable/searchformat.html#query-format>`_.
So this is a first example:

.. sourcecode:: http

    GET /persons?filter=[{"name":"name","op":"eq","val":"John"}] HTTP/1.1
    Accept: application/vnd.api+json

In this example we want to retrieve person records for people named John. So we can see that the filtering interface completely fits that of SQLAlchemy: a list a filter information.

    :name: the name of the field you want to filter on
    :op: the operation you want to use (all SQLAlchemy operations are available)
    :val: the value that you want to compare. You can replace this by "field" if you want to compare against the value of another field

Example with field:

.. sourcecode:: http

    GET /persons?filter=[{"name":"name","op":"eq","field":"birth_date"}] HTTP/1.1
    Accept: application/vnd.api+json

In this example, we want to retrieve people whose name is equal to their birth_date. This example is absurd, it's just here to explain the syntax of this kind of filter.

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

    When you filter on relationships use the "any" operator for "to many" relationships and the "has" operator for "to one" relationships.

There is a shortcut to achieve the same filtering:

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
        "or": [
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
    ] HTTP/1.1
    Accept: application/vnd.api+json

Common available operators:

* any: used to filter on "to many" relationships
* between: used to filter a field between two values
* endswith: checks if field ends with a string
* eq: checks if field is equal to something
* ge: checks if field is greater than or equal to something
* gt: checks if field is greater than something
* has: used to filter on "to one" relationships
* ilike: checks if field contains a string (case insensitive)
* in\_: checks if field is in a list of values
* is\_: checks if field is a value
* isnot: checks if field is not a value
* like: checks if field contains a string
* le: checks if field is less than or equal to something
* lt: checks if field is less than something
* match: checks if field matches against a string or pattern
* ne: checks if field is not equal to something
* notilike: checks if field does not contain a string (case insensitive)
* notin\_: checks if field is not in a list of values
* notlike: checks if field does not contain a string
* startswith: checks if field starts with a string

.. note::

    Available operators depend on the field type in your model

Simple filters
--------------

Simple filters add support for a simplified form of filters and support only the *eq* operator.
Each simple filter is transformed into a full filter and appended to the list of filters.

For example

.. sourcecode:: http

    GET /persons?filter[name]=John HTTP/1.1
    Accept: application/vnd.api+json

equals:

.. sourcecode:: http

    GET /persons?filter=[{"name":"name","op":"eq","val":"John"}] HTTP/1.1
    Accept: application/vnd.api+json


You can also use more than one simple filter in a request:

.. sourcecode:: http

    GET /persons?filter[name]=John&filter[gender]=male HTTP/1.1
    Accept: application/vnd.api+json

which is equal to:

.. sourcecode:: http

    GET /persons?filter=[{"name":"name","op":"eq","val":"John"}, {"name":"gender","op":"eq","val":"male"}] HTTP/1.1
