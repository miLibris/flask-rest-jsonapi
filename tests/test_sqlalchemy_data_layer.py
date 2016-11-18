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

from flask_rest_jsonapi import ResourceList


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


@pytest.fixture
def base_query(item_cls):
    def get_base_query(self, **view_kwargs):
        return self.session.query(item_cls)
    yield get_base_query


@pytest.fixture
def dummy_decorator():
    def deco(f):
        def wrapper_f(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper_f
    yield deco


@pytest.fixture
def item_schema():
    class ItemSchema(Schema):
        class Meta:
            type_ = 'item'
            self_view = 'item_detail'
            self_view_kwargs = {'item_id': '<id>'}
            self_view_many = 'rest_api.item_list'
        id = fields.Str(dump_only=True)
        title = fields.Str()
        content = fields.Str()
        created = fields.DateTime()
    yield ItemSchema


@pytest.fixture
def item_list_resource(session, item_cls, base_query, dummy_decorator, item_schema):
    class ItemList(ResourceList):
        class Meta:
            data_layer = {'name': 'sqlalchemy',
                          'kwargs': {'model': item_cls, 'session': session},
                          'get_base_query': base_query}
            get_decorators = [dummy_decorator]
            post_decorators = [dummy_decorator]
        resource_type = 'item'
        schema_cls = item_schema
        collection_endpoint = 'rest_api.item_list'
    yield ItemList


def test_get_list_resource(client, item_list_resource):
    rest_api = Blueprint('rest_api', __name__)
    rest_api.add_url_rule('/items', view_func=item_list_resource.as_view('item_list'))

    client.application.register_blueprint(rest_api)

    querystring = urlencode({'page[number]': 3,
                             'page[size]': 1,
                             'fields[item]': 'title,content',
                             'sort': '-created,title',
                             'filter[item]': json.dumps([{'field': 'created', 'op': 'gt', 'value': '2016-11-10'}])})
    response = client.get('/items' + '?' + querystring)
    assert response.status_code == 200
