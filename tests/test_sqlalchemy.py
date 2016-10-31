import datetime

import pytest
from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from jsonapi_utils.alchemy import paginate_query, sort_query
from jsonapi_utils.querystring import QueryStringManager

Base = declarative_base()


class Article(Base):

    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    number = Column(Integer, default=0)


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Article.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


@pytest.fixture
def articles(session):
    articles_list = []
    for i in range(0, 200):
        a = Article(number=i)
        articles_list.append(a)
    session.add_all(articles_list)
    session.commit()


@pytest.fixture
def querystring_sort():
    return QueryStringManager({'sort': '-created_at,-number'})


@pytest.fixture
def querystring_paginate():
    return QueryStringManager({'page[size]': '10', 'page[number]': 2})


def test_paginate_query(session, articles, querystring_paginate):
    query = session.query(Article)
    query = paginate_query(query, querystring_paginate.pagination)
    results = query.all()
    assert len(results) == 10
    assert results[0].number == 10


def test_sort_query(session, articles, querystring_sort):
    query = session.query(Article)
    query = sort_query(query, querystring_sort.sorting)
    results = query.all()
    assert results[0].number == 199
