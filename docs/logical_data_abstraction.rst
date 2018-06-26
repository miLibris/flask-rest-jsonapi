.. _logical_data_abstraction:

Logical data abstraction
========================

.. currentmodule:: flask_rest_jsonapi

The first thing to do in Flask-REST-JSONAPI is to create a logical data abstraction. This part of the api discribes schemas of resources exposed by the api that is not the exact mapping of data architecture. The declaration of schemas is made by `Marshmallow <https://marshmallow.readthedocs.io/en/latest/>`_ / `marshmallow-jsonapi <https://marshmallow-jsonapi.readthedocs.io/>`_. Marshmallow is a very popular serialization / deserialization library that offers a lot of features to abstract your data architecture. Moreover there is an other library called marshmallow-jsonapi that fit the JSONAPI 1.0 specification and provides Flask integration.

Example:

In this example, let's assume that we have 2 legacy models Person and Computer and we want to create an abstraction over them.

.. code-block:: python

    from flask_sqlalchemy import SQLAlchemy

    db = SQLAlchemy()

    class Person(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String)
        email = db.Column(db.String)
        birth_date = db.Column(db.String)
        password = db.Column(db.String)


    class Computer(db.Model):
        computer_id = db.Column(db.Integer, primary_key=True)
        serial = db.Column(db.String)
        person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
        person = db.relationship('Person', backref=db.backref('computers'))

Now let's create the logical abstraction to illustrate this concept.

.. code-block:: python

    from marshmallow_jsonapi.flask import Schema, Relationship
    from marshmallow_jsonapi import fields

    class PersonSchema(Schema):
        class Meta:
            type_ = 'person'
            self_view = 'person_detail'
            self_view_kwargs = {'id': '<id>'}
            self_view_many = 'person_list'

        id = fields.Integer(as_string=True, dump_only=True)
        name = fields.Str(required=True, load_only=True)
        email = fields.Email(load_only=True)
        birth_date = fields.Date()
        display_name = fields.Function(lambda obj: "{} <{}>".format(obj.name.upper(), obj.email))
        computers = Relationship(self_view='person_computers',
                                 self_view_kwargs={'id': '<id>'},
                                 related_view='computer_list',
                                 related_view_kwargs={'id': '<id>'},
                                 many=True,
                                 schema='ComputerSchema',
                                 type_='computer',
                                 id_field='computer_id')


    class ComputerSchema(Schema):
        class Meta:
            type_ = 'computer'
            self_view = 'computer_detail'
            self_view_kwargs = {'id': '<id>'}

        id = fields.Str(as_string=True, dump_only=True, attribute='computer_id')
        serial = fields.Str(required=True)
        owner = Relationship(attribute='person',
                             self_view='computer_person',
                             self_view_kwargs={'id': '<id>'},
                             related_view='person_detail',
                             related_view_kwargs={'computer_id': '<id>'},
                             schema='PersonSchema',
                             type_='person')

You can see several differences between models and schemas exposed by the api.

First, take a look of Person compared to PersonSchema:

* we can see that Person has an attribute named "password" and we don't want to expose it through the api so it is not set in PersonSchema
* PersonSchema has an attribute named "display_name" that is the result of concatenation of name and email
* In the computers Relationship() defined on PersonSchema we have set the id_field to "computer_id" as that is the primary key on the Computer(db.model). Without seeting id_field the relationship looks for a field called "id".

Second, take a look of Computer compared to ComputerSchema:

* we can see that attribute computer_id is exposed as id for concictency of the api
* we can see that person relationship between Computer and Person is exposed in ComputerSchema as owner because it is more explicit

As a result you can see that you can expose your data through a very flexible way to create the api of your choice over your data architecture.
