import pytest

from jsonapi_utils.querystring import QueryStringManager


@pytest.fixture
def valid_querystring():
    return {
        'fields[test]': 'one,two',
        'fields[other]': 'other',
        'filter[test]': 'active',
        'filter[other]': 'published',
        'page[number]': '25',
        'page[size]': '10',
        'page[offset]': '100',
        'page[limit]': '200',
        'sort': '-created_at,author.name',
        'include': 'author'
    }


@pytest.fixture
def invalid_querystring():
    return "test=1&fields[test]=2"


@pytest.fixture
def qs_manager(valid_querystring):
    return QueryStringManager(valid_querystring)


def test_querystringmanager_should_instanciate(valid_querystring):
    QueryStringManager(valid_querystring)


def test_quertstringmanage_should_raise_error(invalid_querystring):
    with pytest.raises(ValueError):
        QueryStringManager(invalid_querystring)


def test_querystring_property():
    qs = QueryStringManager({'fields[test]': 'titi,tata', 'filter[testing]': '1', 'testing': '1'})
    assert qs.querystring == {'fields[test]': 'titi,tata', 'filter[testing]': '1'}


def test_filters(qs_manager):
    wanted = {
        'test': ['active'],
        'other': ['published']
    }
    assert qs_manager.filters == wanted


def test_pagination(qs_manager):
    wanted = {
        'number': '25',
        'size': '10',
        'offset': '100',
        'limit': '200'
    }
    assert qs_manager.pagination == wanted


def test_fields(qs_manager):
    wanted = {
        'test': ['one', 'two'],
        'other': ['other']
    }
    assert qs_manager.fields == wanted


def test_sorting(qs_manager):
    wanted = [
        {'field': 'created_at', 'order': 'desc', 'raw': '-created_at'},
        {'field': 'author.name', 'order': 'asc', 'raw': 'author.name'}
    ]
    assert qs_manager.sorting == wanted


def test_include(qs_manager):
    wanted = [
        'author'
    ]
    assert qs_manager.include == wanted
