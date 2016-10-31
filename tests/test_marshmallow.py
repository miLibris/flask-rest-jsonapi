# -*- coding: utf-8 -*-

import pytest

from jsonapi_utils.querystring import QueryStringManager
from jsonapi_utils.marshmallow import paginate_result


@pytest.fixture
def querystring():
    return QueryStringManager({'page[number]': 2, 'page[size]': 2})


@pytest.fixture
def querystring_without_page_number():
    return QueryStringManager({'page[size]': 2})


def test_paginate_result(querystring):
    data = {}
    paginate_result(data, 10, querystring, '/test')
    assert data.get('links') is not None


def test_paginate_result_without_page_number(querystring_without_page_number):
    data = {}
    paginate_result(data, 10, querystring_without_page_number, 'test')
    assert data.get('links') is not None
