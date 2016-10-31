import datetime

import pytest
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from jsonapi_utils.alchemy import paginate_query, sort_query
from jsonapi_utils.querystring import QueryStringManager

Base = declarative_base()


class Item(Base):

    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    number = Column(Integer, default=0)


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
def items(session):
    items_list = []
    for i in range(0, 200):
        item = Item(number=i)
        items_list.append(item)
    session.add_all(items_list)
    session.commit()


@pytest.fixture
def querystring_sort():
    return QueryStringManager({'sort': '-created_at,-number'})


@pytest.fixture
def querystring_paginate():
    return QueryStringManager({'page[size]': '10', 'page[number]': 2})


def test_paginate_query(session, items, querystring_paginate):
    query = session.query(Item)
    query = paginate_query(query, querystring_paginate.pagination)
    results = query.all()
    assert len(results) == 10
    assert results[0].number == 10


def test_sort_query(session, items, querystring_sort):
    query = session.query(Item)
    query = sort_query(query, querystring_sort.sorting)
    results = query.all()
    assert results[0].number == 199
