.. jsonapi-utils documentation master file, created by
   sphinx-quickstart on Fri Oct 21 14:33:15 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Flask-Rest-JSONAPI documentation !
=============================================

Flask-Rest-JSONAPI is a library that help you build rest api.
It is built around:
    - `jsonapi <http://jsonapi.org/>`_: a specification for building apis in json
    - `flask <http://flask.pocoo.org/>`_: a microframework for Python based on Werkzeug
    - `marshmallow-jsonapi <https://marshmallow-jsonapi.readthedocs.io/en/latest/>`_: JSON API 1.0 formatting with
      `marshmallow <https://marshmallow.readthedocs.io/en/latest/>`_
    - `sqlalchemy <http://www.sqlalchemy.org/>`_: SQLAlchemy is the Python SQL toolkit and Object Relational Mapper that
      gives application developers the full power and flexibility of SQL.
    - `mongodb <https://www.mongodb.com/>`_: a free and open-source cross-platform document-oriented database program

I have created this library because i was looking for the best way to implement rest api. The jsonapi specification is
a very strong specification about interactions between the api and the caller and i think it is a very good one.

There is a lot of very good rest library based on flask like `Flask-RESTful <https://github.com/flask-restful/flask-restful>`_
or `Flask-Restless <https://github.com/jfinkels/flask-restless>`_ but i would like to combine the flexibility of Flask-RESTful
with the simplicity of Flask-Restless and the power of marshmallow and SQLAlchemy around a strong and sharable communication
protocol: jsonapi.

Moreover, in most flask frameworks, the only ORM supported is SQLAlchemy so i would like to create an generic
abstraction to communicate with data provider: the data layer system.
Availalble data layers:
    - SQLAlchemy
    - MongoDB
You can easily create and use your own data layer to communicate with the data provider of your choice. Read the data layer section to lean more.

Here is a quick example:

.. code:: python

    from flask import Flask
    from flask_rest_jsonapi import Api, ResourceDetail

    app = Flask(__name__)
    api = Api(app)


    class HelloWorld(ResourceDetail):
        def get(self):
            return "Hello world"

    api.detail_route('index', '/', resource_cls=HelloWorld)

    if __name__ == '__main__':
      app.run(debug=True)

Save this file as api.py

Launch local server:

.. code:: bash

    $ python api.py
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
     * Restarting with stat


Now you can try this:

.. code:: bash

    $ curl "http://127.0.0.1:5000/" -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"
    "Hello world"

.. Note::
   All code examples in this tutorial are based on classic blog example with topic and post.


Contents
--------

.. toctree::
   :maxdepth: 2
   :glob:

   install
   resource
   data_layer
   sorting
   fields_restriction
   filtering
   pagination
   routing
   tutorial



Api reference
-------------

* :ref:`genindex`
* :ref:`modindex`
