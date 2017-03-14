.. _quickstart:

Quickstart
==========

.. currentmodule:: flask_rest_jsonapi

It's time to write your first REST API. This guide assumes you have a working understanding of `Flask <http://flask.pocoo.org>`_, and that you have already installed both Flask and Flask-REST-JSONAPI. If not, then follow the steps in the :ref:`installation` section.

In this section you will learn basic usage of Flask-REST-JSONAPI around a small tutorial that use the SQLAlchemy data layer. This tutorial show you an example of a person and his computers.

First example
-------------

An example of Flask-REST-JSONAPI API looks like this

.. code-block:: python

    # -*- coding: utf-8 -*-

    from flask import Flask
    from flask_rest_jsonapi import Api, ResourceDetail, ResourceList, ResourceRelationship
    from flask_sqlalchemy import SQLAlchemy
    from marshmallow_jsonapi.flask import Schema, Relationship
    from marshmallow_jsonapi import fields

    # Create the Flask application
    app = Flask(__name__)
    app.config['DEBUG'] = True


    # Initialize SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    db = SQLAlchemy(app)


    # Create data storage
    class Person(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String)
        birth_date = db.Column(db.Date)


    class Computer(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        serial = db.Column(db.String)
        person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
        person = db.relationship('Person', backref=db.backref('computers'))

    db.create_all()


    # Create logical data abstraction (same as data storage for this first example)
    class PersonSchema(Schema):
        class Meta:
            type_ = 'person'
            self_view = 'person_detail'
            self_view_kwargs = {'id': '<id>'}
            self_view_many = 'person_list'

        id = fields.Str(dump_only=True)
        name = fields.Str()
        birth_date = fields.Date()
        computers = Relationship(self_view='person_computers',
                                 self_view_kwargs={'id': '<id>'},
                                 related_view='computer_list',
                                 related_view_kwargs={'id': '<id>'},
                                 many=True,
                                 schema='ComputerSchema',
                                 type_='computer')


    class ComputerSchema(Schema):
        class Meta:
            type_ = 'computer'
            self_view = 'computer_detail'
            self_view_kwargs = {'id': '<id>'}

        id = fields.Str(dump_only=True)
        serial = fields.Str()


    # Create resource managers
    class PersonList(ResourceList):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}


    class PersonDetail(ResourceDetail):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}


    class PersonRelationship(ResourceRelationship):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}


    class ComputerList(ResourceList):
        def query(self, **view_kwargs):
            query_ = self.session.query(Computer)
            if view_kwargs.get('id') is not None:
                query_ = query_.join(Person).filter_by(id=view_kwargs['id'])
            return query_

        def before_create_object(self, data, **view_kwargs):
            if view_kwargs.get('id') is not None:
                try:
                    person = self.session.query(Person).filter_by(id=view_kwargs['id']).one()
                except NoResultFound:
                    raise JsonApiException({'parameter': 'id'},
                                           'Person: {} not found'.format(view_kwargs['id']),
                                           title='ObjectNotFound',
                                           status='404')
                else:
                    data['person_id'] = person.id

        schema = ComputerSchema
        data_layer = {'session': db.session,
                      'model': Computer,
                      'methods': {'query': query,
                                  'before_create_object': before_create_object}}


    class ComputerDetail(ResourceDetail):
        schema = ComputerSchema
        data_layer = {'session': db.session,
                      'model': Computer}


    # Create endpoints
    api = Api(app)
    api.route(PersonList, 'person_list', '/persons')
    api.route(PersonDetail, 'person_detail', '/persons/<int:id>')
    api.route(PersonRelationship, 'person_computers', '/persons/<int:id>/relationships/computers')
    api.route(ComputerList, 'computer_list', '/computers', '/persons/<int:id>/computers')
    api.route(ComputerDetail, 'computer_detail', '/computers/<int:id>')

    if __name__ == '__main__':
        # Start application
        app.run(debug=True)

This example provides this api

========================================  ======  ================  =====================================================
url                                       method  endpoint          action
========================================  ======  ================  =====================================================
/persons                                  GET     person_list       Retrieve a collection of persons
/persons                                  POST    person_list       Create a person
/persons/<int:id>                         GET     person_detail     Retrieve details of a person
/persons/<int:id>                         PATCH   person_detail     Update a person
/persons/<int:id>                         DELETE  person_detail     Delete a person
/persons/<int:id>/relationship/computers  GET     person_computers  Retrieve relationships between a person and computers
/persons/<int:id>/relationship/computers  POST    person_computers  Create relationships between a person and computers
/persons/<int:id>/relationship/computers  PATCH   person_computers  Update relationships between a person and computers
/persons/<int:id>/relationship/computers  DELETE  person_computers  Delete relationships between a person and computers
/computers                                GET     computer_list     Retrieve a collection of computers
/computers                                POST    computer_list     Create a computer
/persons/<int:id>/computers               GET     computer_list     Retrieve a collection computers related to a person
/persons/<int:id>/computers               POST    computer_list     Create a computer related to a person
/computers/<int:id>                       GET     computer_detail   Retrieve details of a computer
/computers/<int:id>                       PATCH   computer_detail   Update a computer
/computers/<int:id>                       DELETE  computer_detail   Delete a computer
========================================  ======  ================  =====================================================

.. warning::

    In this example, I use Flask-SQLAlchemy so you have to install it before to run the example.

    $ pip install flask_sqlalchemy

Save this as api.py and run it using your Python interpreter. Note that we've enabled
`Flask debugging <http://flask.pocoo.org/docs/quickstart/#debug-mode>`_ mode to provide code reloading and better error
messages. ::

    $ python api.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader

.. warning::

    Debug mode should never be used in a production environment!

Classical CRUD operations
-------------------------

Create a computer
~~~~~~~~~~~~~~~~~

Request

.. sourcecode:: http

    POST /computers HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json
 
    {
      "data": {
        "type": "computer",
        "attributes": {
          "serial": "Amstrad"
        }
      }
    }

Response

.. sourcecode:: http

    HTTP/1.1 201 Created
    Content-Type: application/vnd.api+json

    {
      "data": {
        "type": "computer",
        "id": "1",
        "attributes": {
          "serial": "Amstrad",
        },
        "links": {
          "self": "/computers/1"
        }
      },
      "links": {
        "self": "/computers/1"
      },
      "jsonapi": {
        "version": "1.0"
      }
    }

List computers
~~~~~~~~~~~~~~

Request

.. sourcecode:: http

    GET /computers HTTP/1.1
    Accept: application/vnd.api+json

Response

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
      "data": [
        {
          "type": "computer",
          "id": "1",
          "attributes": {
            "serial": "Amstrad",
          },
          "links": {
            "self": "/computers/1"
          }
        }
      ],
      "links": {
        "self": "/computers"
      },
      "jsonapi": {
        "version": "1.0"
      }
    }

Update the computer
~~~~~~~~~~~~~~~~~~~

Request

.. sourcecode:: http

    PATCH /computers/1 HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json

    {
      "data": {
        "type": "computer",
        "id": "1"
        "attributes": {
          "serial": "Amstrad 2"
        }
      }
    }

Request

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
      "data": {
        "type": "computer",
        "id": "1",
        "attributes": {
          "serial": "Amstrad 2",
        },
        "links": {
          "self": "/computers/1"
        },
        "jsonapi": {
          "version": "1.0"
        }
      }
    }

Delete the computer
~~~~~~~~~~~~~~~~~~~

Request

.. sourcecode:: http

    DELETE /computers/1 HTTP/1.1
    Accept: application/vnd.api+json

Response

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
      "meta": {
        "Object successful deleted"
      },
      "jsonapi": {
        "version": "1.0"
      }
    }

Relationships
-------------

Now let's use relationships tools. First, create 3 computers called Halo, Nestor and Comodor like in previous example.
Done ?
Ok. So let's continue this tutorial. We assume that Halo has id: 2, Nestor id: 3 and Comodor has id 4.

Create a person with related computer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Request

.. sourcecode:: http

    POST /persons?include=computers HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json
 
    {
      "data": {
        "type": "person",
        "attributes": {
          "name": "John",
          "birth_date": "1990-12-18"
        },
        "relationships": {
          "computers": {
            "data": [
              {
                "type": "computer",
                "id": "2"
              }
            ]
          }
        }
      }
    }

Response

.. sourcecode:: http

    HTTP/1.1 201 Created
    Content-Type: application/vnd.api+json

    {
      "data": {
        "type": "person"
        "id": "1",
        "attributes": {
          "birth_date": "1990-12-18",
          "name": "John"
        },
        "relationships": {
          "computers": {
            "data": [
              {
                "id": "2",
                "type": "computer"
              }
            ],
            "links": {
              "related": "/persons/1/computers",
              "self": "/persons/1/relationship/computers"
            }
          }
        },
        "links": {
          "self": "/persons/1"
        },
      },
      "included": [
        {
          "type": "computer"
          "id": "2",
          "attributes": {
            "serial": "Amstrad"
          },
          "links": {
            "self": "/computers/2"
          },
        }
      ],
      "jsonapi": {
        "version": "1.0"
      },
      "links": {
        "self": "/persons/1"
      }
    }

You can see that I have added the querystring parameter "include" to the url

.. sourcecode:: http

    POST /persons?include=computers HTTP/1.1

Thanks to this parameter related computers details are included to the result. If you want to learn more:
include_related_

Update relationships between a person and computers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now John sell his Amstrad and buy a new computer called Nestor (id: 3). So we want to link this new computer to John. John have also made a mistake in his birth_date so let's update this 2 things in the same time.

Request

.. sourcecode:: http

    PATCH /persons/1?include=computers HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json
 
    {
      "data": {
        "type": "person",
        "id": "1",
        "attributes": {
          "birth_date": "1990-10-18"
        },
        "relationships": {
          "computers": {
            "data": [
              {
                "type": "computer",
                "id": "3"
              }
            ]
          }
        }
      }
    }

Response

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
      "data": {
        "type": "person"
        "id": "1",
        "attributes": {
          "birth_date": "1990-10-18",
          "name": "John"
        },
        "links": {
          "self": "/persons/1"
        },
        "relationships": {
          "computers": {
            "data": [
              {
                "id": "3",
                "type": "computer"
              }
            ],
            "links": {
              "related": "/persons/1/computers",
              "self": "/persons/1/relationship/computers"
            }
          }
        },
      },
      "included": [
        {
          "type": "computer"
          "id": "3",
          "attributes": {
            "serial": "Nestor"
          },
          "links": {
            "self": "/computers/3"
          },
        }
      ],
      "links": {
        "self": "/persons/2"
      },
      "jsonapi": {
        "version": "1.0"
      }
    }

Add computer to a person
~~~~~~~~~~~~~~~~~~~~~~~~

Now John buy a new computer called Comodor so let's link it to John.

Request

.. sourcecode:: http

    POST /persons/1/relationships/computers HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json
 
    {
      "data": [
        {
          "type": "computer",
          "id": "4"
        }
      ]
    }

Response

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
      "data": {
        "type": "person",
        "id": "1",
        "attributes": {
          "name": "John",
          "birth_date": "1990-10-18"
        },
        "links": {
          "self": "/persons/1"
        },
        "relationships": {
          "computers": {
            "data": [
              {
                "id": "3",
                "type": "computer"
              },
              {
                "id": "4",
                "type": "computer"
              }
            ],
            "links": {
              "related": "/persons/1/computers",
              "self": "/persons/1/relationships/computers"
            }
          }
        }
      },
      "included": [
        {
          "type": "computer",
          "id": "3",
          "attributes": {
            "serial": "Nestor"
          },
          "links": {
            "self": "/computers/3"
          }
        },
        {
          "type": "computer",
          "id": "4",
          "attributes": {
            "serial": "Comodor"
          },
          "links": {
            "self": "/computers/4"
          }
        }
      ],
      "jsonapi": {
        "version": "1.0"
      },
      "links": {
        "self": "/persons/1/relationships/computers"
      }
    }


Remove relationship between a computer and a person
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now John sell his old Nestor computer so let's unlink it from John.

Request

.. sourcecode:: http

    DELETE /persons/1/relationships/computers HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json
 
    {
      "data": [
        {
          "type": "computer",
          "id": "3"
        }
      ]
    }

Response

.. sourcecode:: http

    HTTP/1.1 200 OK
    Content-Type: application/vnd.api+json

    {
    "data": {
        "type": "person",
        "id": "1",
        "attributes": {
            "name": "John",
            "birth_date": "1990-10-18"
        },
        "links": {
            "self": "/persons/1"
        },
        "relationships": {
            "computers": {
                "data": [
                    {
                        "id": "4",
                        "type": "computer"
                    }
                ],
                "links": {
                    "related": "/persons/1/computers",
                    "self": "/persons/1/relationships/computers"
                }
            }
        }
    },
    "included": [
        {
            "type": "computer",
            "id": "4",
            "attributes": {
                "serial": "Comodor"
            },
            "links": {
                "self": "/computers/4"
            }
        }
    ],
    "jsonapi": {
        "version": "1.0"
    },
    "links": {
        "self": "/persons/1/relationships/computers"
    }
}
