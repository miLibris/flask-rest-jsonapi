.. _errors:

Errors
======

.. currentmodule:: flask_rest_jsonapi

JSONAPI 1.0 specification recommand to return errors like that:

.. sourcecode:: http

    HTTP/1.1 422 Unprocessable Entity
    Content-Type: application/vnd.api+json

    {
      "errors": [
        {
          "status": "422",
          "source": {
            "pointer":"/data/attributes/first-name"
          },
          "title":  "Invalid Attribute",
          "detail": "First name must contain at least three characters."
        }
      ],
      "jsonapi": {
        "version": "1.0"
      }
    }

The "source" field gives information about the error if it is located in data provided or in querystring parameter.

The previous example displays error located in data provided instead of this next example displays error located in querystring parameter "include":

.. sourcecode:: http

    HTTP/1.1 400 Bad Request
    Content-Type: application/vnd.api+json

    {
      "errors": [
        {
          "status": "400",
          "source": {
            "parameter": "include"
          },
          "title":  "BadRequest",
          "detail": "Include parameter is invalid"
        }
      ],
      "jsonapi": {
        "version": "1.0"
      }
    }

Flask-REST-JSONAPI provides two kind of helpers to achieve error displaying:

| * **the errors module**: you can import jsonapi_errors from the `errors module <https://github.com/miLibris/flask-rest-jsonapi/blob/master/flask_rest_jsonapi/errors.py>`_ to create the structure of a list of errors according to JSONAPI 1.0 specification
|
| * **the exceptions module**: you can import lot of exceptions from this `module <https://github.com/miLibris/flask-rest-jsonapi/blob/master/flask_rest_jsonapi/exceptions.py>`_ that helps you to raise exceptions that will be well formatted according to JSONAPI 1.0 specification

When you create custom code for your api I recommand to use exceptions from exceptions module of Flask-REST-JSONAPI to raise errors because JsonApiException based exceptions are catched and rendered according to JSONAPI 1.0 specification.

Example:

.. code-block:: python

    # all required imports are not displayed in this example
    from flask_rest_jsonapi.exceptions import ObjectNotFound

    class ComputerList(ResourceList):
        def query(self, view_kwargs):
            query_ = self.session.query(Computer)
            if view_kwargs.get('id') is not None:
                try:
                    self.session.query(Person).filter_by(id=view_kwargs['id']).one()
                except NoResultFound:
                    raise ObjectNotFound({'parameter': 'id'}, "Person: {} not found".format(view_kwargs['id']))
                else:
                    query_ = query_.join(Person).filter(Person.id == view_kwargs['id'])
            return query_
