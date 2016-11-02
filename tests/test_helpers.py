# -*- coding: utf-8 -*-

import pytest

from flask import request
from marshmallow_jsonapi.flask import Schema
from marshmallow_jsonapi import fields
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from jsonapi_utils.helpers import jsonapi_list, jsonapi_detail

Base = declarative_base()


class Item(Base):

    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Item.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def item_schema_kls():
    class ItemSchema(Schema):
        class Meta:
            type_ = 'item'
        id = fields.Str()

    return ItemSchema


@pytest.fixture
def query(session):
    return session.query(Item)


@pytest.fixture
def items(session):
    item = Item()
    session.add(item)
    session.commit()


def test_list(item_schema_kls, query, app):
    with app.test_request_context():
        request.args = {'fields[item]': 'id', 'sort': 'id'}
        result = jsonapi_list('item', item_schema_kls, Item, query, 'test')
        assert result is not None


def test_detail_not_found(item_schema_kls, query, app, session):
    with app.test_request_context():
        request.args = {'fields[item]': 'id'}
        result = jsonapi_detail('item', item_schema_kls, Item, 'id', 1, session)
        assert result[1] == 404


def test_detail(item_schema_kls, query, app, session, items):
    with app.test_request_context():
        request.args = {'fields[item]': 'id'}
        result = jsonapi_detail('item', item_schema_kls, Item, 'id', 1, session)
        assert result is not None
