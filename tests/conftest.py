# -*- coding: utf-8 -*-

import pytest
from flask import Blueprint
from flask import Flask
from flask import make_response
from marshmallow import Schema as MarshmallowSchema
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema, Relationship
from sqlalchemy import create_engine, Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from flapison import Api, ResourceList, ResourceDetail, ResourceRelationship, JsonApiException


@pytest.fixture(scope="function")
def app():
    app = Flask(__name__)
    return app

@pytest.fixture(scope="function")
def api(api_blueprint):
    return Api(blueprint=api_blueprint)

@pytest.yield_fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def base():
    return declarative_base()


@pytest.fixture(scope="function")
def person_tag_model(base):
    class Person_Tag(base):
        __tablename__ = 'person_tag'

        id = Column(Integer, ForeignKey('person.person_id'), primary_key=True, index=True)
        key = Column(String, primary_key=True)
        value = Column(String, primary_key=True)

    yield Person_Tag


@pytest.fixture(scope="function")
def person_single_tag_model(base):
    class Person_Single_Tag(base):
        __tablename__ = 'person_single_tag'

        id = Column(Integer, ForeignKey('person.person_id'), primary_key=True, index=True)
        key = Column(String)
        value = Column(String)

    yield Person_Single_Tag


@pytest.fixture(scope="function")
def string_json_attribute_person_model(base):
    """
    This approach to faking JSON support for testing with sqlite is borrowed from:
    https://avacariu.me/articles/2016/compiling-json-as-text-for-sqlite-with-sqlalchemy
    """
    import sqlalchemy.types as types
    import json

    class StringyJSON(types.TypeDecorator):
        """Stores and retrieves JSON as TEXT."""

        impl = types.TEXT

        def process_bind_param(self, value, dialect):
            if value is not None:
                value = json.dumps(value)
            return value

        def process_result_value(self, value, dialect):
            if value is not None:
                value = json.loads(value)
            return value

    # TypeEngine.with_variant says "use StringyJSON instead when
    # connecting to 'sqlite'"
    MagicJSON = types.JSON().with_variant(StringyJSON, 'sqlite')

    class StringJsonAttributePerson(base):

        __tablename__ = 'string_json_attribute_person'

        person_id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        birth_date = Column(DateTime)
        # This model uses a String type for "json_tags" to avoid dependency on a nonstandard SQL type in testing, \
        # while still demonstrating support
        address = Column(MagicJSON)

    yield StringJsonAttributePerson


@pytest.fixture()
def person_model(base):
    class Person(base):
        __tablename__ = 'person'

        person_id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        birth_date = Column(DateTime)
        computers = relationship("Computer", back_populates="person")
        tags = relationship("Person_Tag", cascade="save-update, merge, delete, delete-orphan")
        single_tag = relationship("Person_Single_Tag", uselist=False,
                                  cascade="save-update, merge, delete, delete-orphan")

    yield Person


@pytest.fixture()
def computer_model(base):
    class Computer(base):
        __tablename__ = 'computer'

        id = Column(Integer, primary_key=True)
        serial = Column(String, nullable=False)
        person_id = Column(Integer, ForeignKey('person.person_id'))

        person = relationship("Person", back_populates="computers")

    yield Computer


@pytest.fixture(scope="function")
def engine(person_tag_model, person_single_tag_model, person_model, computer_model, string_json_attribute_person_model):
    engine = create_engine("sqlite:///:memory:")
    person_tag_model.metadata.create_all(engine)
    person_single_tag_model.metadata.create_all(engine)
    person_model.metadata.create_all(engine)
    computer_model.metadata.create_all(engine)
    string_json_attribute_person_model.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture()
def person(session, person_model, computer, person_tag_model, person_single_tag_model):
    person_ = person_model(name='test')
    session_ = session
    session_.add(person_)
    session_.commit()
    yield person_
    session_.delete(person_)
    session_.commit()


@pytest.fixture()
def person_2(session, person_model, computer, person_tag_model, person_single_tag_model):
    person_ = person_model(name='test2')
    session_ = session
    session_.add(person_)
    session_.commit()
    yield person_
    session_.delete(person_)
    session_.commit()


@pytest.fixture()
def computer(session, computer_model, person_model):
    computer_ = computer_model(serial='1')
    session_ = session
    session_.add(computer_)
    session_.commit()
    yield computer_
    session_.delete(computer_)
    session_.commit()


@pytest.fixture(scope="function")
def dummy_decorator():
    def deco(f):
        def wrapper_f(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapper_f

    yield deco


@pytest.fixture(scope="function")
def person_tag_schema():
    class PersonTagSchema(MarshmallowSchema):
        class Meta:
            type_ = 'person_tag'

        id = fields.Str(dump_only=True, load_only=True)
        key = fields.Str()
        value = fields.Str()

    yield PersonTagSchema


@pytest.fixture(scope="function")
def person_single_tag_schema():
    class PersonSingleTagSchema(MarshmallowSchema):
        class Meta:
            type_ = 'person_single_tag'

        id = fields.Str(dump_only=True, load_only=True)
        key = fields.Str()
        value = fields.Str()

    yield PersonSingleTagSchema


@pytest.fixture(scope="function")
def address_schema():
    class AddressSchema(MarshmallowSchema):
        street = fields.String(required=True)
        city = fields.String(required=True)
        state = fields.String(missing='NC')
        zip = fields.String(required=True)

    yield AddressSchema


@pytest.fixture(scope="function")
def string_json_attribute_person_schema(address_schema):
    class StringJsonAttributePersonSchema(Schema):
        class Meta:
            type_ = 'string_json_attribute_person'
            self_view = 'api.string_json_attribute_person_detail'
            self_view_kwargs = {'person_id': '<id>'}

        id = fields.Integer(as_string=True, attribute='person_id')
        name = fields.Str(required=True)
        birth_date = fields.DateTime()
        address = fields.Nested(address_schema, many=False)

    yield StringJsonAttributePersonSchema


@pytest.fixture(scope="function")
def person_schema(person_tag_schema, person_single_tag_schema):
    class PersonSchema(Schema):
        class Meta:
            type_ = 'person'
            self_view = 'api.person_detail'
            self_view_kwargs = {'person_id': '<id>'}

        id = fields.Integer(as_string=True, attribute='person_id')
        name = fields.Str(required=True)
        birth_date = fields.DateTime()
        computers = Relationship(related_view='api.computer_list',
                                 related_view_kwargs={'person_id': '<person_id>'},
                                 schema='ComputerSchema',
                                 type_='computer',
                                 many=True)

        tags = fields.Nested(person_tag_schema, many=True)
        single_tag = fields.Nested(person_single_tag_schema)

    yield PersonSchema


@pytest.fixture(scope="function")
def computer_schema():
    class ComputerSchema(Schema):
        class Meta:
            type_ = 'computer'
            self_view = 'api.computer_detail'
            self_view_kwargs = {'id': '<id>'}

        id = fields.Integer(as_string=True, dump_only=True)
        serial = fields.Str(required=True)
        owner = Relationship(attribute='person',
                             default=None,
                             missing=None,
                             related_view='api.person_detail',
                             related_view_kwargs={'person_id': '<person.person_id>'},
                             schema='PersonSchema',
                             id_field='person_id',
                             type_='person')

    yield ComputerSchema


@pytest.fixture(scope="function")
def before_create_object():
    def before_create_object_(self, data, view_kwargs):
        pass

    yield before_create_object_


@pytest.fixture(scope="function")
def before_update_object():
    def before_update_object_(self, obj, data, view_kwargs):
        pass

    yield before_update_object_


@pytest.fixture(scope="function")
def before_delete_object():
    def before_delete_object_(self, obj, view_kwargs):
        pass

    yield before_delete_object_


@pytest.fixture(scope="function")
def person_list(session, person_model, dummy_decorator, person_schema, before_create_object):
    class PersonList(ResourceList):
        schema = person_schema
        data_layer = {'model': person_model,
                      'session': session,
                      'mzthods': {'before_create_object': before_create_object}}
        get_decorators = [dummy_decorator]
        post_decorators = [dummy_decorator]
        get_schema_kwargs = dict()
        post_schema_kwargs = dict()

    yield PersonList


@pytest.fixture(scope="function")
def person_detail(session, person_model, dummy_decorator, person_schema, before_update_object, before_delete_object):
    class PersonDetail(ResourceDetail):
        schema = person_schema
        data_layer = {'model': person_model,
                      'session': session,
                      'url_field': 'person_id',
                      'methods': {'before_update_object': before_update_object,
                                  'before_delete_object': before_delete_object}}
        get_decorators = [dummy_decorator]
        patch_decorators = [dummy_decorator]
        delete_decorators = [dummy_decorator]
        get_schema_kwargs = dict()
        patch_schema_kwargs = dict()
        delete_schema_kwargs = dict()

    yield PersonDetail


@pytest.fixture(scope="function")
def person_computers(session, person_model, dummy_decorator, person_schema):
    class PersonComputersRelationship(ResourceRelationship):
        schema = person_schema
        data_layer = {'session': session,
                      'model': person_model,
                      'url_field': 'person_id'}
        get_decorators = [dummy_decorator]
        post_decorators = [dummy_decorator]
        patch_decorators = [dummy_decorator]
        delete_decorators = [dummy_decorator]

    yield PersonComputersRelationship


@pytest.fixture(scope="function")
def person_list_raise_jsonapiexception():
    class PersonList(ResourceList):
        def get(self):
            raise JsonApiException('', '')

    yield PersonList


@pytest.fixture(scope="function")
def person_list_raise_exception():
    class PersonList(ResourceList):
        def get(self):
            raise Exception()

    yield PersonList


@pytest.fixture(scope="function")
def person_list_response():
    class PersonList(ResourceList):
        def get(self):
            return make_response('')

    yield PersonList


@pytest.fixture(scope="function")
def person_list_without_schema(session, person_model):
    class PersonList(ResourceList):
        data_layer = {'model': person_model,
                      'session': session}

        def get(self):
            return make_response('')

    yield PersonList


@pytest.fixture(scope="function")
def query():
    def query_(self, view_kwargs):
        if view_kwargs.get('person_id') is not None:
            return self.session.query(computer_model).join(person_model).filter_by(person_id=view_kwargs['person_id'])
        return self.session.query(computer_model)

    yield query_


@pytest.fixture(scope="function")
def computer_list(session, computer_model, computer_schema, query):
    class ComputerList(ResourceList):
        schema = computer_schema
        data_layer = {'model': computer_model,
                      'session': session,
                      'methods': {'query': query}}

    yield ComputerList


@pytest.fixture(scope="function")
def computer_detail(session, computer_model, dummy_decorator, computer_schema):
    class ComputerDetail(ResourceDetail):
        schema = computer_schema
        data_layer = {'model': computer_model,
                      'session': session}
        methods = ['GET', 'PATCH']

    yield ComputerDetail


@pytest.fixture(scope="function")
def computer_owner(session, computer_model, dummy_decorator, computer_schema):
    class ComputerOwnerRelationship(ResourceRelationship):
        schema = computer_schema
        data_layer = {'session': session,
                      'model': computer_model}

    yield ComputerOwnerRelationship


@pytest.fixture(scope="function")
def string_json_attribute_person_detail(session, string_json_attribute_person_model,
                                        string_json_attribute_person_schema):
    class StringJsonAttributePersonDetail(ResourceDetail):
        schema = string_json_attribute_person_schema
        data_layer = {'session': session,
                      'model': string_json_attribute_person_model}

    yield StringJsonAttributePersonDetail


@pytest.fixture(scope="function")
def string_json_attribute_person_list(session, string_json_attribute_person_model, string_json_attribute_person_schema):
    class StringJsonAttributePersonList(ResourceList):
        schema = string_json_attribute_person_schema
        data_layer = {'session': session,
                      'model': string_json_attribute_person_model}

    yield StringJsonAttributePersonList


@pytest.fixture(scope="function")
def api_blueprint(client):
    bp = Blueprint('api', __name__)
    yield bp


@pytest.fixture(scope="function")
def register_routes(client, api, app, api_blueprint, person_list, person_detail, person_computers,
                    person_list_raise_jsonapiexception, person_list_raise_exception, person_list_response,
                    person_list_without_schema, computer_list, computer_detail, computer_owner,
                    string_json_attribute_person_detail, string_json_attribute_person_list):
    api.route(person_list, 'person_list', '/persons')
    api.route(person_detail, 'person_detail', '/persons/<int:person_id>')
    api.route(person_computers, 'person_computers', '/persons/<int:person_id>/relationships/computers')
    api.route(person_computers, 'person_computers_owned', '/persons/<int:person_id>/relationships/computers-owned')
    api.route(person_computers, 'person_computers_error', '/persons/<int:person_id>/relationships/computer')
    api.route(person_list_raise_jsonapiexception, 'person_list_jsonapiexception', '/persons_jsonapiexception')
    api.route(person_list_raise_exception, 'person_list_exception', '/persons_exception')
    api.route(person_list_response, 'person_list_response', '/persons_response')
    api.route(person_list_without_schema, 'person_list_without_schema', '/persons_without_schema')
    api.route(computer_list, 'computer_list', '/computers', '/persons/<int:person_id>/computers')
    api.route(computer_list, 'computer_detail', '/computers/<int:id>')
    api.route(computer_owner, 'computer_owner', '/computers/<int:id>/relationships/owner')
    api.route(string_json_attribute_person_list, 'string_json_attribute_person_list', '/string_json_attribute_persons')
    api.route(string_json_attribute_person_detail, 'string_json_attribute_person_detail',
              '/string_json_attribute_persons/<int:person_id>')
    api.init_app(app)


@pytest.fixture(scope="function")
def get_object_mock():
    class get_object(object):
        foo = type('foo', (object,), {
            'property': type('prop', (object,), {
                'mapper': type('map', (object,), {
                    'class_': 'test'
                })()
            })()
        })()

        def __init__(self, kwargs):
            pass

    return get_object


@pytest.fixture(scope="function")
def wrong_data_layer():
    class WrongDataLayer(object):
        pass

    yield WrongDataLayer
