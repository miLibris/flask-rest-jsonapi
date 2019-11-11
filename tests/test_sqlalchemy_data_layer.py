# -*- coding: utf-8 -*-

from csv import DictWriter, DictReader
from io import StringIO

import pytest
from flask import Blueprint, json
from flask import make_response
from marshmallow import Schema as MarshmallowSchema
from marshmallow import ValidationError
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema, Relationship
from six.moves.urllib.parse import urlencode, parse_qs
from sqlalchemy import create_engine, Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import flapison.decorators
import flapison.resource
import flapison.schema
from flapison import Api, ResourceList, ResourceDetail, ResourceRelationship, JsonApiException
from flapison.data_layers.alchemy import SqlalchemyDataLayer
from flapison.data_layers.base import BaseDataLayer
from flapison.data_layers.filtering.alchemy import Node
from flapison.exceptions import RelationNotFound, InvalidSort, InvalidFilters, InvalidInclude, BadRequest
from flapison.pagination import add_pagination_links
from flapison.querystring import QueryStringManager as QSManager


def test_add_pagination_links(app):
    with app.app_context():
        qs = {'page[number]': '2', 'page[size]': '10'}
        qsm = QSManager(qs, None)
        pagination_dict = dict()
        add_pagination_links(pagination_dict, 43, qsm, str())
        last_page_dict = parse_qs(pagination_dict['links']['last'][1:])
        assert len(last_page_dict['page[number]']) == 1
        assert last_page_dict['page[number]'][0] == '5'


def test_Node(person_model, person_schema, monkeypatch):
    from copy import deepcopy
    filt = {
        'val': '0000',
        'field': True,
        'not': dict(),
        'name': 'name',
        'op': 'eq',
        'strip': lambda: 's'
    }
    filt['not'] = deepcopy(filt)
    del filt['not']['not']
    n = Node(person_model,
             filt,
             None,
             person_schema)
    with pytest.raises(TypeError):
        # print(n.val is None and n.field is None)
        # # n.column
        n.resolve()
    with pytest.raises(AttributeError):
        n.model = None
        n.column
    with pytest.raises(InvalidFilters):
        n.model = person_model
        n.filter_['op'] = ''
        n.operator
    with pytest.raises(InvalidFilters):
        n.related_model
    with pytest.raises(InvalidFilters):
        n.related_schema


def test_check_method_requirements(monkeypatch):
    self = type('self', (object,), dict())
    request = type('request', (object,), dict(method='GET'))
    monkeypatch.setattr(flapison.decorators, 'request', request)
    with pytest.raises(Exception):
        flapison.decorators.check_method_requirements(lambda: 1)(self())


def test_json_api_exception():
    JsonApiException(None, None, title='test', status='test')


def test_query_string_manager(person_schema):
    query_string = {'page[slumber]': '3'}
    qsm = QSManager(query_string, person_schema)
    with pytest.raises(BadRequest):
        qsm.pagination
    qsm.qs['sort'] = 'computers'
    with pytest.raises(InvalidSort):
        qsm.sorting


@pytest.mark.skip('Monkey patching the request class stops the header parsing and breaks content negotiation')
def test_resource(app, person_model, person_schema, session, monkeypatch):
    def schema_load_mock(*args):
        raise ValidationError(dict(errors=[dict(status=None, title=None)]))

    with app.app_context():
        query_string = {'page[slumber]': '3'}
        app = type('app', (object,), dict(config=dict(DEBUG=True)))
        headers = {'Content-Type': 'application/vnd.api+json'}
        request = type('request', (object,), dict(method='POST',
                                                  headers=headers,
                                                  get_json=dict,
                                                  args=query_string))
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        rl = ResourceList()
        rd = ResourceDetail()
        rl._data_layer = dl
        rl.schema = person_schema
        rd._data_layer = dl
        rd.schema = person_schema
        monkeypatch.setattr(flapison.resource, 'request', request)
        monkeypatch.setattr(flapison.decorators, 'current_app', app)
        monkeypatch.setattr(flapison.decorators, 'request', request)
        monkeypatch.setattr(rl.schema, 'load', schema_load_mock)
        r = super(flapison.resource.Resource, ResourceList) \
            .__new__(ResourceList)
        with pytest.raises(Exception):
            r.dispatch_request()
        rl.post()
        rd.patch()


def test_compute_schema(person_schema):
    query_string = {'page[number]': '3', 'fields[person]': list()}
    qsm = QSManager(query_string, person_schema)
    with pytest.raises(InvalidInclude):
        flapison.schema.compute_schema(person_schema, dict(), qsm, ['id'])
    flapison.schema.compute_schema(person_schema, dict(only=list()), qsm, list())


def test_compute_schema_propagate_context(person_schema, computer_schema):
    query_string = {}
    qsm = QSManager(query_string, person_schema)
    schema = flapison.schema.compute_schema(person_schema, dict(), qsm, ['computers'])
    assert schema.declared_fields['computers'].__dict__['_Relationship__schema'].__dict__['context'] == dict()
    schema = flapison.schema.compute_schema(person_schema, dict(context=dict(foo='bar')), qsm, ['computers'])
    assert schema.declared_fields['computers'].__dict__['_Relationship__schema'].__dict__['context'] == dict(foo='bar')


# test good cases
def test_get_list(client, register_routes, person, person_2):
    with client:
        querystring = urlencode({
            'page[number]': 1,
            'page[size]': 1,
            'fields[person]': 'name,birth_date',
            'sort': '-name',
            'include': 'computers.owner',
            'filter': json.dumps(
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
                ])
        })
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']



def test_get_list_with_simple_filter(client, register_routes, person, person_2):
    with client:
        querystring = urlencode({'page[number]': 1,
                                 'page[size]': 1,
                                 'fields[person]': 'name,birth_date',
                                 'sort': '-name',
                                 'filter[name]': 'test'
                                 })
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']



def test_get_list_disable_pagination(client, register_routes):
    with client:
        querystring = urlencode({'page[size]': 0})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_head_list(client, register_routes):
    with client:
        response = client.head('/persons', content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_post_list(client, register_routes, computer):
    payload = {
        'data': {
            'type': 'person',
            'attributes': {
                'name': 'test'
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.post('/persons', data=json.dumps(payload), content_type='application/vnd.api+json')
        assert response.status_code == 201, response.json['errors']



def test_post_list_nested_no_join(client, register_routes, computer):
    payload = {
        'data': {
            'type': 'string_json_attribute_person',
            'attributes': {
                'name': 'test_name',
                'address': {
                    'street': 'test_street',
                    'city': 'test_city',
                    'state': 'NC',
                    'zip': '00000'
                }
            }
        }
    }
    with client:
        response = client.post('/string_json_attribute_persons', data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        print(response.get_data())
        assert response.status_code == 201, response.json['errors']
        assert json.loads(response.get_data())['data']['attributes']['address']['street'] == 'test_street'


def test_post_list_nested(client, register_routes, computer):
    payload = {
        'data': {
            'type': 'person',
            'attributes': {
                'name': 'test',
                'tags': [
                    {'key': 'k1', 'value': 'v1'},
                    {'key': 'k2', 'value': 'v2'}
                ]
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.post('/persons', data=json.dumps(payload), content_type='application/vnd.api+json')
        assert response.status_code == 201, response.json['errors']
        assert json.loads(response.get_data())['data']['attributes']['tags'][0]['key'] == 'k1'


def test_post_list_single(client, register_routes, person):
    payload = {
        'data': {
            'type': 'computer',
            'attributes': {
                'serial': '1'
            },
            'relationships': {
                'owner': {
                    'data': {
                        'type': 'person',
                        'id': str(person.person_id)
                    }
                }
            }
        }
    }

    with client:
        response = client.post('/computers', data=json.dumps(payload), content_type='application/vnd.api+json')
        assert response.status_code == 201, response.json['errors']


def test_get_detail(client, register_routes, person):
    with client:
        response = client.get('/persons/' + str(person.person_id), content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']



def test_patch_detail(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': str(person.person_id),
            'type': 'person',
            'attributes': {
                'name': 'test2'
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id),
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_patch_detail_nested(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': str(person.person_id),
            'type': 'person',
            'attributes': {
                'name': 'test2',
                'tags': [
                    {'key': 'new_key', 'value': 'new_value'}
                ],
                'single_tag': {'key': 'new_single_key', 'value': 'new_single_value'}
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id),
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']
        response_dict = json.loads(response.get_data())
        assert response_dict['data']['attributes']['tags'][0]['key'] == 'new_key'
        assert response_dict['data']['attributes']['single_tag']['key'] == 'new_single_key'


def test_delete_detail(client, register_routes, person):
    with client:
        response = client.delete('/persons/' + str(person.person_id), content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_get_relationship(session, client, register_routes, computer, person):
    session_ = session
    person.computers = [computer]
    session_.commit()

    with client:
        response = client.get('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                              content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_get_relationship_empty(client, register_routes, person):
    with client:
        response = client.get('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                              content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_get_relationship_single(session, client, register_routes, computer, person):
    session_ = session
    computer.person = person
    session_.commit()

    with client:
        response = client.get('/computers/' + str(computer.id) + '/relationships/owner',
                              content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_get_relationship_single_empty(session, client, register_routes, computer):
    with client:
        response = client.get('/computers/' + str(computer.id) + '/relationships/owner',
                              content_type='application/vnd.api+json')
        response_json = json.loads(response.get_data())
        assert None is response_json['data']
        assert response.status_code == 200, response.json['errors']


def test_issue_49(session, client, register_routes, person, person_2):
    with client:
        for p in [person, person_2]:
            response = client.get('/persons/' + str(p.person_id) + '/relationships/computers?include=computers',
                                  content_type='application/vnd.api+json')
            assert response.status_code == 200, response.json['errors']
            assert (json.loads(response.get_data()))['links']['related'] == '/persons/' + str(
                p.person_id) + '/computers'


def test_post_relationship(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'computer',
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.post('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_post_relationship_not_list(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'person',
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.post('/computers/' + str(computer.id) + '/relationships/owner',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_patch_relationship(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'computer',
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_patch_relationship_single(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'person',
            'id': str(person.person_id)
        }
    }
    with client:
        response = client.patch('/computers/' + str(computer.id) + '/relationships/owner',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_delete_relationship(session, client, register_routes, computer, person):
    session_ = session
    person.computers = [computer]
    session_.commit()

    payload = {
        'data': [
            {
                'type': 'computer',
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.delete('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_delete_relationship_single(session, client, register_routes, computer, person):
    session_ = session
    computer.person = person
    session_.commit()

    payload = {
        'data': {
            'type': 'person',
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.delete('/computers/' + str(computer.id) + '/relationships/owner',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_get_list_response(client, register_routes):
    with client:
        response = client.get('/persons_response', content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


# test various Accept headers
def test_single_accept_header(client, register_routes):
    with client:
        response = client.get('/persons', content_type='application/vnd.api+json',
                              headers={'Accept': 'application/vnd.api+json'})
        assert response.status_code == 200, response.json['errors']


def test_multiple_accept_header(client, register_routes):
    with client:
        response = client.get('/persons', content_type='application/vnd.api+json',
                              headers={'Accept': '*/*, application/vnd.api+json, application/vnd.api+json;q=0.9'})
        assert response.status_code == 200, response.json['errors']


@pytest.mark.skip('This is accepted using the workzeug parser')
def test_wrong_accept_header(client, register_routes):
    with client:
        response = client.get('/persons', content_type='application/vnd.api+json',
                              headers={'Accept': 'application/vnd.api+json;q=0.7, application/vnd.api+json;q=0.9'})
        assert response.status_code == 406, response.json['errors']


# test Content-Type error
def test_wrong_content_type(client, register_routes):
    with client:
        response = client.post('/persons', headers={'Content-Type': 'application/vnd.api+json;q=0.8'})
        assert response.status_code == 415, response.json['errors']


@pytest.fixture(scope="module")
def wrong_data_layer():
    class WrongDataLayer(object):
        pass

    yield WrongDataLayer


def test_wrong_data_layer_inheritence(wrong_data_layer):
    with pytest.raises(Exception):
        class PersonDetail(ResourceDetail):
            data_layer = {'class': wrong_data_layer}

        PersonDetail()


def test_wrong_data_layer_kwargs_type():
    with pytest.raises(Exception):
        class PersonDetail(ResourceDetail):
            data_layer = list()

        PersonDetail()


def test_get_list_jsonapiexception(client, register_routes):
    with client:
        response = client.get('/persons_jsonapiexception', content_type='application/vnd.api+json')
        assert response.status_code == 500, response.json['errors']


def test_get_list_exception(client, register_routes):
    with client:
        response = client.get('/persons_exception', content_type='application/vnd.api+json')
        assert response.status_code == 500, response.json['errors']


def test_get_list_without_schema(client, register_routes):
    with client:
        response = client.post('/persons_without_schema', content_type='application/vnd.api+json')
        assert response.status_code == 500, response.json['errors']


def test_get_list_bad_request(client, register_routes):
    with client:
        querystring = urlencode({'page[number': 3})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_invalid_fields(client, register_routes):
    with client:
        querystring = urlencode({'fields[person]': 'error'})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_invalid_include(client, register_routes):
    with client:
        querystring = urlencode({'include': 'error'})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_invalid_filters_parsing(client, register_routes):
    with client:
        querystring = urlencode({'filter': 'error'})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_invalid_page(client, register_routes):
    with client:
        querystring = urlencode({'page[number]': 'error'})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_invalid_sort(client, register_routes):
    with client:
        querystring = urlencode({'sort': 'error'})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_detail_object_not_found(client, register_routes):
    with client:
        response = client.get('/persons/3', content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_post_relationship_related_object_not_found(client, register_routes, person):
    payload = {
        'data': [
            {
                'type': 'computer',
                'id': '2'
            }
        ]
    }

    with client:
        response = client.post('/persons/' + str(person.person_id) + '/relationships/computers',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 404, response.json['errors']


def test_get_relationship_relationship_field_not_found(client, register_routes, person):
    with client:
        response = client.get('/persons/' + str(person.person_id) + '/relationships/computer',
                              content_type='application/vnd.api+json')
        assert response.status_code == 500, response.json['errors']


def test_get_list_invalid_filters_val(client, register_routes):
    with client:
        querystring = urlencode({'filter': json.dumps([{'name': 'computers', 'op': 'any'}])})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_name(client, register_routes):
    with client:
        querystring = urlencode({'filter': json.dumps([{'name': 'computers__serial', 'op': 'any', 'val': '1'}])})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 200, response.json['errors']


def test_get_list_no_name(client, register_routes):
    with client:
        querystring = urlencode({'filter': json.dumps([{'op': 'any', 'val': '1'}])})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_no_op(client, register_routes):
    with client:
        querystring = urlencode({'filter': json.dumps([{'name': 'computers__serial', 'val': '1'}])})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_attr_error(client, register_routes):
    with client:
        querystring = urlencode({'filter': json.dumps([{'name': 'error', 'op': 'eq', 'val': '1'}])})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_get_list_field_error(client, register_routes):
    with client:
        querystring = urlencode({'filter': json.dumps([{'name': 'name', 'op': 'eq', 'field': 'error'}])})
        response = client.get('/persons' + '?' + querystring, content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_sqlalchemy_data_layer_without_session(person_model, person_list):
    with pytest.raises(Exception):
        SqlalchemyDataLayer(dict(model=person_model, resource=person_list))


def test_sqlalchemy_data_layer_without_model(session, person_list):
    with pytest.raises(Exception):
        SqlalchemyDataLayer(dict(session=session, resource=person_list))


def test_sqlalchemy_data_layer_create_object_error(session, person_model, person_list):
    with pytest.raises(JsonApiException):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model, resource=person_list))
        dl.create_object(dict(), dict())


def test_sqlalchemy_data_layer_get_object_error(session, person_model):
    with pytest.raises(Exception):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model, id_field='error'))
        dl.get_object(dict())


def test_sqlalchemy_data_layer_update_object_error(session, person_model, person_list, monkeypatch):
    def commit_mock():
        raise JsonApiException()

    with pytest.raises(JsonApiException):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model, resource=person_list))
        monkeypatch.setattr(dl.session, 'commit', commit_mock)
        dl.update_object(dict(), dict(), dict())


def test_sqlalchemy_data_layer_delete_object_error(session, person_model, person_list, monkeypatch):
    def commit_mock():
        raise JsonApiException()

    def delete_mock(obj):
        pass

    with pytest.raises(JsonApiException):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model, resource=person_list))
        monkeypatch.setattr(dl.session, 'commit', commit_mock)
        monkeypatch.setattr(dl.session, 'delete', delete_mock)
        dl.delete_object(dict(), dict())


def test_sqlalchemy_data_layer_create_relationship_field_not_found(session, person_model):
    with pytest.raises(Exception):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        dl.create_relationship(dict(), 'error', '', dict(id=1))


def test_sqlalchemy_data_layer_create_relationship_error(session, person_model, get_object_mock, monkeypatch):
    def commit_mock():
        raise JsonApiException()

    with pytest.raises(JsonApiException):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        monkeypatch.setattr(dl.session, 'commit', commit_mock)
        monkeypatch.setattr(dl, 'get_object', get_object_mock)
        dl.create_relationship(dict(data=None), 'foo', '', dict(id=1))


def test_sqlalchemy_data_layer_get_relationship_field_not_found(session, person_model, person):
    with pytest.raises(RelationNotFound):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        dl.get_relationship('error', '', '', dict(id=1))


def test_sqlalchemy_data_layer_update_relationship_field_not_found(session, person_model):
    with pytest.raises(Exception):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        dl.update_relationship(dict(), 'error', '', dict(id=1))


def test_sqlalchemy_data_layer_update_relationship_error(session, person_model, get_object_mock, monkeypatch):
    def commit_mock():
        raise JsonApiException()

    with pytest.raises(JsonApiException):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        monkeypatch.setattr(dl.session, 'commit', commit_mock)
        monkeypatch.setattr(dl, 'get_object', get_object_mock)
        dl.update_relationship(dict(data=None), 'foo', '', dict(id=1))


def test_sqlalchemy_data_layer_delete_relationship_field_not_found(session, person_model):
    with pytest.raises(Exception):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        dl.delete_relationship(dict(), 'error', '', dict(id=1))


def test_sqlalchemy_data_layer_delete_relationship_error(session, person_model, get_object_mock, monkeypatch):
    def commit_mock():
        raise JsonApiException()

    with pytest.raises(JsonApiException):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        monkeypatch.setattr(dl.session, 'commit', commit_mock)
        monkeypatch.setattr(dl, 'get_object', get_object_mock)
        dl.delete_relationship(dict(data=None), 'foo', '', dict(id=1))


def test_sqlalchemy_data_layer_sort_query_error(session, person_model, monkeypatch):
    with pytest.raises(InvalidSort):
        dl = SqlalchemyDataLayer(dict(session=session, model=person_model))
        dl.sort_query(None, [dict(field='test')])


def test_post_list_incorrect_type(client, register_routes, computer):
    payload = {
        'data': {
            'type': 'error',
            'attributes': {
                'name': 'test'
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.post('/persons', data=json.dumps(payload), content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_post_list_validation_error(client, register_routes, computer):
    payload = {
        'data': {
            'type': 'person',
            'attributes': {},
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.post('/persons', data=json.dumps(payload), content_type='application/vnd.api+json')
        assert response.status_code == 422, response.json['errors']


def test_patch_detail_incorrect_type(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': str(person.person_id),
            'type': 'error',
            'attributes': {
                'name': 'test2'
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id),
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_patch_detail_validation_error(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': str(person.person_id),
            'type': 'person',
            'attributes': {
                'name': {'test2': 'error'}
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id),
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 422, response.json['errors']


def test_patch_detail_missing_id(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'person',
            'attributes': {
                'name': 'test2'
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id),
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_patch_detail_wrong_id(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': 'error',
            'type': 'person',
            'attributes': {
                'name': 'test2'
            },
            'relationships': {
                'computers': {
                    'data': [
                        {
                            'type': 'computer',
                            'id': str(computer.id)
                        }
                    ]
                }
            }
        }
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id),
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 422, response.json['errors']


def test_post_relationship_no_data(client, register_routes, computer, person):
    with client:
        response = client.post('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                               data=json.dumps(dict()),
                               content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_post_relationship_not_list_missing_type(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.post('/computers/' + str(computer.id) + '/relationships/owner',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_post_relationship_not_list_missing_id(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'person'
        }
    }

    with client:
        response = client.post('/computers/' + str(computer.id) + '/relationships/owner',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_post_relationship_not_list_wrong_type(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'error',
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.post('/computers/' + str(computer.id) + '/relationships/owner',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_post_relationship_missing_type(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.post('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_post_relationship_missing_id(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'computer',
            }
        ]
    }

    with client:
        response = client.post('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_post_relationship_wrong_type(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'error',
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.post('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                               data=json.dumps(payload),
                               content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_patch_relationship_no_data(client, register_routes, computer, person):
    with client:
        response = client.patch('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                data=json.dumps(dict()),
                                content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_patch_relationship_not_list_missing_type(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.patch('/computers/' + str(computer.id) + '/relationships/owner',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_patch_relationship_not_list_missing_id(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'person'
        }
    }

    with client:
        response = client.patch('/computers/' + str(computer.id) + '/relationships/owner',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_patch_relationship_not_list_wrong_type(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'error',
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.patch('/computers/' + str(computer.id) + '/relationships/owner',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_patch_relationship_missing_type(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_patch_relationship_missing_id(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'computer',
            }
        ]
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_patch_relationship_wrong_type(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'error',
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.patch('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                data=json.dumps(payload),
                                content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_delete_relationship_no_data(client, register_routes, computer, person):
    with client:
        response = client.delete('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                 data=json.dumps(dict()),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_delete_relationship_not_list_missing_type(client, register_routes, computer, person):
    payload = {
        'data': {
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.delete('/computers/' + str(computer.id) + '/relationships/owner',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_delete_relationship_not_list_missing_id(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'person'
        }
    }

    with client:
        response = client.delete('/computers/' + str(computer.id) + '/relationships/owner',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_delete_relationship_not_list_wrong_type(client, register_routes, computer, person):
    payload = {
        'data': {
            'type': 'error',
            'id': str(person.person_id)
        }
    }

    with client:
        response = client.delete('/computers/' + str(computer.id) + '/relationships/owner',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_delete_relationship_missing_type(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.delete('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_delete_relationship_missing_id(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'computer',
            }
        ]
    }

    with client:
        response = client.delete('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 400, response.json['errors']


def test_delete_relationship_wrong_type(client, register_routes, computer, person):
    payload = {
        'data': [
            {
                'type': 'error',
                'id': str(computer.id)
            }
        ]
    }

    with client:
        response = client.delete('/persons/' + str(person.person_id) + '/relationships/computers?include=computers',
                                 data=json.dumps(payload),
                                 content_type='application/vnd.api+json')
        assert response.status_code == 409, response.json['errors']


def test_base_data_layer():
    base_dl = BaseDataLayer(dict())
    with pytest.raises(NotImplementedError):
        base_dl.create_object(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.get_object(dict())
    with pytest.raises(NotImplementedError):
        base_dl.get_collection(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.update_object(None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.delete_object(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.create_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.get_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.update_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.delete_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.query(dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_create_object(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_create_object(None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_get_object(dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_get_object(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_get_collection(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_get_collection(None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_update_object(None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_update_object(None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_delete_object(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_delete_object(None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_create_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_create_relationship(None, None, None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_get_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_get_relationship(None, None, None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_update_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_update_relationship(None, None, None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.before_delete_relationship(None, None, None, dict())
    with pytest.raises(NotImplementedError):
        base_dl.after_delete_relationship(None, None, None, None, None, dict())


def test_qs_manager():
    with pytest.raises(ValueError):
        QSManager([], None)


def test_api(app, person_list):
    api = Api(app)
    api.route(person_list, 'person_list', '/persons', '/person_list')
    api.init_app()


def test_api_resources(app, person_list):
    api = Api()
    api.route(person_list, 'person_list2', '/persons', '/person_list')
    api.init_app(app)

def test_api_resources_multiple_route(app, person_list):
    """
    If we use the same resource twice, each instance of that resource should have the
    correct endpoint
    """
    api = Api()

    class DummyResource(ResourceDetail):
        def get(self):
            return self.view

    api.route(DummyResource, 'endpoint1', '/url1')
    api.route(DummyResource, 'endpoint2', '/url2')
    api.init_app(app)

    with app.test_client() as client:
        assert client.get('/url1', content_type='application/vnd.api+json').json == 'endpoint1'
        assert client.get('/url2', content_type='application/vnd.api+json').json == 'endpoint2'

def test_relationship_containing_hyphens(api, app, client, computer_list, person_schema, person_computers, computer_schema, person):
    """
    This is a bit of a hack. Basically, since we can no longer have two attributes that read from the same key
    in Marshmallow 3, we have to create a new Schema and Resource here that name their relationship "computers_owned"
    in order to test hyphenation
    """

    class PersonOwnedSchema(person_schema):
        class Meta:
            exclude = ('computers',)

        computers_owned = Relationship(
            related_view='api.computer_list',
            related_view_kwargs={'person_id': '<person_id>'},
            schema='ComputerSchema',
            type_='computer',
            many=True,
            attribute='computers'
        )

    class PersonComputersOwnedRelationship(person_computers):
        schema = PersonOwnedSchema

    api.route(PersonComputersOwnedRelationship, 'person_computers_owned',
              '/persons/<int:person_id>/relationships/computers-owned')
    api.route(computer_list, 'computer_list', '/computers', '/persons/<int:person_id>/computers')
    api.init_app(app)

    response = client.get('/persons/{}/relationships/computers-owned'.format(person.person_id),
                          content_type='application/vnd.api+json')
    assert response.status_code == 200, response.json['errors']
