# -*- coding: utf-8 -*-

from flask import Flask
from flask_rest_jsonapi import Api, ResourceDetail, ResourceList, ResourceRelationship, JsonApiException
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
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
            query_ = query_.join(Person).filter(Person.id == view_kwargs['id'])
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
