# -*- coding: utf-8 -*-

from six.moves.urllib.parse import urlencode
import pytest
import json

from sqlalchemy import create_engine, Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from flask import Blueprint
from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields

from flask_rest_jsonapi import Api, ResourceList, ResourceDetail


@pytest.fixture(scope="session")
def base():
    yield declarative_base()


@pytest.fixture(scope="session")
def person_model(base):
    class Person(base):

        __tablename__ = 'person'

        person_id = Column(Integer, primary_key=True)
        name = Column(String)
        birth_date = Column(DateTime)

        computers = relationship("Computer", backref="owner")
    yield Person


@pytest.fixture(scope="session")
def computer_model(base):
    class Computer(base):

        __tablename__ = 'computer'

        id = Column(Integer, primary_key=True)
        serial = Column(String)
        person_id = Column(Integer, ForeignKey('person.person_id'))

    yield Computer


@pytest.fixture(scope="session")
def engine(person_model, computer_model):
    engine = create_engine("sqlite:///:memory:")
    person_model.metadata.create_all(engine)
    computer_model.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture(scope="session")
def dummy_decorator():
    def deco(f):
        def wrapper_f(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper_f
    yield deco


@pytest.fixture(scope="session")
def person_schema():
    class PersonSchema(Schema):
        class Meta:
            type_ = 'person'
            self_view = 'api.person_detail'
            self_view_kwargs = {'person_id': '<id>'}
        id = fields.Str(dump_only=True, attribute='person_id')
        name = fields.Str()
        birth_date = fields.DateTime()
        computers = Relationship(self_view='api.person_computers',
                                 self_view_kwargs={'person_id': '<person_id>'},
                                 related_view='api.computer_list',
                                 related_view_kwargs={'person_id': '<person_id>'},
                                 schema='ComputerSchema',
                                 type_='computer')
    yield PersonSchema


@pytest.fixture(scope="session")
def computer_schema():
    class ComputerSchema(Schema):
        class Meta:
            type_ = 'computer'
            self_view = 'api.computer_detail'
            self_view_kwargs = {'id': '<id>'}
        id = fields.Str(dump_only=True, attribute='computer_id')
        serial = fields.Str()
        owner = Relationship(self_view='api.computer_person',
                             self_view_kwargs={'id': '<id>'},
                             related_view='api.person_detail',
                             related_view_kwargs={'person_id': '<owner.person_id>'},
                             schema='PersonSchema',
                             id_field='person_id',
                             type_='person')
    yield ComputerSchema


@pytest.fixture(scope="session")
def before_create_object():
    def base_before_create_object(self, data, **view_kwargs):
        pass
    yield base_before_create_object


@pytest.fixture(scope="session")
def before_update_object():
    def base_before_update_object(self, obj, data, **view_kwargs):
        pass
    yield base_before_update_object


@pytest.fixture(scope="session")
def before_delete_object():
    def base_before_delete_object(self, obj, **view_kwargs):
        pass
    yield base_before_delete_object


@pytest.fixture(scope="session")
def person_list(session, person_model, dummy_decorator, person_schema, before_create_object):
    class PersonList(ResourceList):
        schema = person_schema
        data_layer_kwargs = {'model': person_model, 'session': session}

        class Meta:
            get_decorators = [dummy_decorator]
            post_decorators = [dummy_decorator]
            before_create_object = before_create_object
            get_schema_kwargs = dict()
            post_schema_kwargs = dict()
    yield PersonList


@pytest.fixture(scope="session")
def person_detail(session, person_model, dummy_decorator, person_schema, before_update_object, before_delete_object):
    class PersonDetail(ResourceDetail):
        schema = person_schema
        data_layer_kwargs = {'model': person_model,
                             'session': session,
                             'id_field': 'person_id',
                             'url_field': 'person_id'}

        class Meta:
            get_decorators = [dummy_decorator]
            patch_decorators = [dummy_decorator]
            delete_decorators = [dummy_decorator]
            before_update_object = before_update_object
            before_delete_object = before_delete_object
            get_schema_kwargs = dict()
            patch_schema_kwargs = dict()
            delete_schema_kwargs = dict()
    yield PersonDetail


@pytest.fixture(scope="session")
def base_query(computer_model, person_model):
    def get_base_query(self, **view_kwargs):
        return self.session.query(computer_model).join(person_model).filter_by(person_id=view_kwargs['person_id'])
    yield get_base_query


@pytest.fixture(scope="session")
def computer_list(session, computer_model, computer_schema, base_query):
    class ComputerList(ResourceList):
        schema = computer_schema
        data_layer_kwargs = {'model': computer_model, 'session': session}

        class Meta:
            query = base_query
            not_allowed_methods = ['POST']
            relationship_mapping = {'person': {'relationship_field': 'owner', 'id_field': 'person_id'}}
    yield ComputerList


@pytest.fixture(scope="session")
def computer_detail(session, computer_model, dummy_decorator, computer_schema):
    class ComputerDetail(ResourceDetail):
        schema = computer_schema
        data_layer_kwargs = {'model': computer_model,
                             'session': session}
    yield ComputerDetail


@pytest.fixture(scope="session")
def api_blueprint(client):
    bp = Blueprint('api', __name__)
    yield bp


@pytest.fixture(scope="session")
def register_routes(client, api_blueprint, person_list, person_detail, computer_list, computer_detail):
    api = Api(api_blueprint)
    api.route(person_list, 'person_list', '/persons')
    api.route(person_detail, 'person_detail', '/persons/<int:person_id>')
    api.route(computer_list, 'computer_list', '/persons/<int:person_id>/computers')
    api.route(computer_list, 'computer_detail', '/computers/<int:id>')
    api.init_app(client.application)


def test_wrong_content_type(client, register_routes):
    with client:
        response = client.get('/persons')
        assert response.status_code == 415


def test_wrong_accept_header(client, register_routes):
    with client:
        response = client.get('/persons', content_type='application/vnd.api+json', headers={'Accept': 'error'})
        assert response.status_code == 406


def test_get_list(client, register_routes):
    with client:
        querystring = urlencode({'page[number]': 3,
                                 'page[size]': 1,
                                 'fields[person]': 'name',
                                 'sort': '-name',
                                 'include': 'computers',
                                 'filters': json.dumps(
                                     [
                                         {
                                             'and': [
                                                 {
                                                     'name': 'computers',
                                                     'op': 'any',
                                                     'val': {
                                                         'name': 'serial',
                                                         'op': 'eq',
                                                         'val': '0000'
                                                     }
                                                 },
                                                 {
                                                     'or': [
                                                         {
                                                             'name': 'name',
                                                             'op': 'like',
                                                             'val': '%test%'
                                                         },
                                                         {
                                                             'name': 'name',
                                                             'op': 'like',
                                                             'val': '%test2%'
                                                         }
                                                     ]
                                                 }
                                             ]
                                         }
                                     ])})
        response = client.get('/persons' + '?' + querystring,
                              content_type='application/vnd.api+json')
        assert response.status_code == 200
