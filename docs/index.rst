Flask-REST-JSONAPI
==================

.. module:: flask_rest_jsonapi

**Flask-REST-JSONAPI** is an extension for Flask that adds support for quickly building REST APIs with hudge flexibility around JSONAPI 1.0 specification. It is design to fit the complexity of real life environnement so Flask-REST-JSONAPI helps you to create a logicial abstraction of your data called "resource" and can interface any kind of ORMs or data storage.

Main concepts
-------------

.. image:: img/schema.png
   :width: 600px
   :alt: Architecture

| * **`JSON API 1.0 specification <http://jsonapi.org/>`_**: it is a very popular specification about client server interactions for REST JSON API. It helps you to work in team because it is a very precise and sharable. Thanks to this specification your server will offer lot a features for clients like a strong structure of request and response, filtering, pagination, sparse fieldsets, including related resources, great error formatting etc.
| 
| * **Logical data abstration**: you usually need to expose resources to clients that don't fit your data table architecture. For example sometimes you don't want to expose all attributes of a table or compute additional attribut for a resource or create a resource that use data from multiple data storage. Flask-REST-JSONAPI helps you to create a logical abstraction of your data with `Marshmallow <https://marshmallow.readthedocs.io/en/latest/>`_ / `marshmallow-jsonapi <https://marshmallow-jsonapi.readthedocs.io/>`_ so you can expose your data through a very flexible way.
| 
| * **Data layer**: the data layer is a CRUD interface between your resource manager and your data. Thanks to it you can use any data storage or ORMs. There is an already full featured data layer that use SQLAlchemy ORM but you can create and use your own custom data layer to use data from your own data storage or create a data layer that use multiple data storage. You can even create a data layer that send notifications or make any custom work during CRUD operations.

Features
--------

Flask-REST-JSONAPI has lot of features:

* Powerful filtering
* Pagination
* Sorting
* Sparse fieldsets
* Include related documents
* Relationship management


User's Guide
------------

This part of the documentation will show you how to get started in using
Flask-REST-JSONAPI with Flask.

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   filtering
   pagination
   sorting
   sparse_fieldsets
   include_related_objects
   resource
   data_layer
   routing
   errors

API Reference
-------------

If you are looking for information on a specific function, class or
method, this part of the documentation is for you.

* :ref:`genindex`
* :ref:`modindex`
