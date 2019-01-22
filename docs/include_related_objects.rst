.. _include_related_objects:

Include related objects
=======================

.. currentmodule:: flask_rest_jsonapi

You can include related object(s) details to responses with the querystring parameter named "include". You can use "include" parameter on any kind of route (classical CRUD route or relationships route) and any kind of http methods as long as method return data.

This features will add an additional key in result named "included"

Example:

Request:

.. sourcecode:: http

    GET /persons/1?include=computers HTTP/1.1
    Accept: application/vnd.api+json

Response:

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
      "data": {
        "type": "person",
        "id": "1",
        "attributes": {
          "display_name": "JEAN <jean@gmail.com>",
          "birth_date": "1990-10-10"
        },
        "relationships": {
          "computers": {
            "data": [
              {
                "type": "computer",
                "id": "1"
              }
            ],
            "links": {
              "related": "/persons/1/computers",
              "self": "/persons/1/relationships/computers"
            }
          }
        },
        "links": {
          "self": "/persons/1"
        }
      },
      "included": [
        {
          "type": "computer",
          "id": "1",
          "attributes": {
            "serial": "Amstrad"
          },
          "relationships": {
            "owner": {
              "links": {
                "related": "/computers/1/owner",
                "self": "/computers/1/relationships/owner"
              }
            }
          },
          "links": {
            "self": "/computers/1"
          }
        }
      ],
      "links": {
        "self": "/persons/1"
      },
      "jsonapi": {
        "version": "1.0"
      }
    }

You can even follow relationships with include

Example:

Request:

.. sourcecode:: http

    GET /persons/1?include=computers.owner HTTP/1.1
    Accept: application/vnd.api+json

Response:

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
      "data": {
        "type": "person",
        "id": "1",
        "attributes": {
          "display_name": "JEAN <jean@gmail.com>",
          "birth_date": "1990-10-10"
        },
        "relationships": {
          "computers": {
            "data": [
              {
                "type": "computer",
                "id": "1"
              }
            ],
            "links": {
              "related": "/persons/1/computers",
              "self": "/persons/1/relationships/computers"
            }
          }
        },
        "links": {
          "self": "/persons/1"
        }
      },
      "included": [
        {
          "type": "computer",
          "id": "1",
          "attributes": {
            "serial": "Amstrad"
          },
          "relationships": {
            "owner": {
              "data": {
                "type": "person",
                "id": "1"
              },
              "links": {
                "related": "/computers/1/owner",
                "self": "/computers/1/relationships/owner"
              }
            }
          },
          "links": {
            "self": "/computers/1"
          }
        },
        {
          "type": "person",
          "id": "1",
          "attributes": {
            "display_name": "JEAN <jean@gmail.com>",
            "birth_date": "1990-10-10"
          },
          "relationships": {
            "computers": {
              "links": {
                "related": "/persons/1/computers",
                "self": "/persons/1/relationships/computers"
              }
            }
          },
          "links": {
            "self": "/persons/1"
          }
        }
      ],
      "links": {
        "self": "/persons/1"
      },
      "jsonapi": {
        "version": "1.0"
      }
    }

I know it is an absurd example because it will include details of related person computers and details of the person that is already in the response. But it is just for example.
