from jsonapi_utils.querystring import QueryStringManager


def test_querystring_property():
    qs = QueryStringManager({'fields[test]': 'titi,tata', 'filter[testing]': '1', 'testing': '1'})
    assert qs.querystring == {'fields[test]': 'titi,tata', 'filter[testing]': '1'}
