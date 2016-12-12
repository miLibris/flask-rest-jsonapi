# -*- coding: utf-8 -*-

from six.moves.urllib.parse import urlencode
import pytest
import json
import datetime

from sqlalchemy import create_engine, Column, Integer, DateTime, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask import Blueprint
from marshmallow_jsonapi.flask import Schema
from marshmallow_jsonapi import fields

from flask_rest_jsonapi import ResourceList, ResourceDetail, SqlalchemyDataLayer


@pytest.fixture(scope="session")
def base():
    yield declarative_base()


@pytest.fixture(scope="session")
def item_cls(base):
    class Item(base):

        __tablename__ = 'item'

        id = Column(Integer, primary_key=True)
        title = Column(String)
        content = Column(String)
        created = Column(DateTime, default=datetime.datetime.utcnow)
    yield Item


@pytest.fixture(scope="session")
def engine(item_cls):
    engine = create_engine("sqlite:///:memory:")
    item_cls.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture(scope="session")
def base_query(item_cls):
    def get_base_query(self, **view_kwargs):
        return self.session.query(item_cls)
    yield get_base_query


@pytest.fixture(scope="session")
def dummy_decorator():
    def deco(f):
        def wrapper_f(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper_f
    yield deco


@pytest.fixture(scope="session")
def item_schema():
    class ItemSchema(Schema):
        class Meta:
            type_ = 'item'
            self_view = 'rest_api.item_detail'
            self_view_kwargs = {'item_id': '<id>'}
            self_view_many = 'rest_api.item_list'
        id = fields.Str(dump_only=True)
        title = fields.Str()
        content = fields.Str()
        created = fields.DateTime()
    yield ItemSchema


@pytest.fixture(scope="session")
def item_list_resource(session, item_cls, base_query, dummy_decorator, item_schema):
    class ItemList(ResourceList):
        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'model': item_cls, 'session': session},
                          'get_base_query': base_query}
            get_decorators = [dummy_decorator]
            post_decorators = [dummy_decorator]
        resource_type = 'item'
        schema = {'cls': item_schema}
        endpoint = {'name': 'rest_api.item_list'}
    yield ItemList


@pytest.fixture(scope="session")
def item_detail_resource(session, item_cls, base_query, dummy_decorator, item_schema):
    class ItemDetail(ResourceDetail):
        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'model': item_cls,
                                     'session': session,
                                     'id_field': 'id',
                                     'url_param_name': 'item_id'},
                          'get_base_query': base_query}
            get_decorators = [dummy_decorator]
            patch_decorators = [dummy_decorator]
            delete_decorators = [dummy_decorator]
        resource_type = 'item'
        schema = {'cls': item_schema}
    yield ItemDetail


@pytest.fixture(scope="session")
def item_list_resource_not_allowed(session, item_cls, base_query, dummy_decorator, item_schema):
    class ItemList(ResourceList):
        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'model': item_cls, 'session': session},
                          'get_base_query': base_query}
            get_decorators = [dummy_decorator]
            not_allowed_methods = ['POST']
        resource_type = 'item'
        schema_cls = item_schema
        collection_endpoint = 'rest_api.item_list'
    yield ItemList


@pytest.fixture(scope="session")
def rest_api_blueprint(client):
    bp = Blueprint('rest_api', __name__)
    yield bp


@pytest.fixture(scope="session")
def register_routes(client, rest_api_blueprint, item_list_resource, item_detail_resource,
                    item_list_resource_not_allowed):
    rest_api_blueprint.add_url_rule('/items', view_func=item_list_resource.as_view('item_list'))
    rest_api_blueprint.add_url_rule('/items/<int:item_id>', view_func=item_detail_resource.as_view('item_detail'))
    rest_api_blueprint.add_url_rule('/items_not_allowed',
                                    view_func=item_list_resource_not_allowed.as_view('item_list_not_allowed'))
    client.application.register_blueprint(rest_api_blueprint)


def test_get_list_resource(client, register_routes):
    querystring = urlencode({'page[number]': 3,
                             'page[size]': 1,
                             'fields[item]': 'title,content',
                             'sort': '-created,title',
                             'filter[item]': json.dumps([{'field': 'created', 'op': 'gt', 'value': '2016-11-10'}])})
    response = client.get('/items' + '?' + querystring,
                          content_type='application/vnd.api+json')
    assert response.status_code == 200


def test_post_list_resource(client, register_routes):
    response = client.post('/items',
                           data=json.dumps({"data": {"type": "item", "attributes": {"title": "test"}}}),
                           content_type='application/vnd.api+json')
    assert response.status_code == 201


def test_get_detail_resource(client, register_routes):
    response = client.get('/items/1', content_type='application/vnd.api+json')
    assert response.status_code == 200


def test_patch_patch_resource(client, register_routes):
    response = client.patch('/items/1',
                            data=json.dumps({"data": {"type": "item", "id": 1, "attributes": {"title": "test2"}}}),
                            content_type='application/vnd.api+json')
    assert response.status_code == 200


def test_delete_detail_resource(client, register_routes):
    response = client.delete('/items/1', content_type='application/vnd.api+json')
    assert response.status_code == 204


def test_post_list_resource_not_allowed(client, register_routes):
    response = client.post('/items_not_allowed',
                           data=json.dumps({"data": {"type": "item", "attributes": {"title": "test"}}}),
                           content_type='application/vnd.api+json')
    assert response.status_code == 405


def test_get_detail_resource_not_found(client, register_routes):
    response = client.get('/items/2', content_type='application/vnd.api+json')
    assert response.status_code == 404


def test_patch_patch_resource_error(client, register_routes):
    response = client.patch('/items/1',
                            data=json.dumps({"data": {"type": "item", "attributes": {"title": "test2"}}}),
                            content_type='application/vnd.api+json')
    assert response.status_code == 422


def test_wrong_content_type(client, register_routes):
    response = client.delete('/items/1')
    assert response.status_code == 415


def test_response_content_type(client, register_routes):
    response = client.delete('/items/1', content_type='application/vnd.api+json')
    assert response.headers['Content-Type'] == 'application/vnd.api+json'
