# -*- coding: utf-8 -*-

from flask import request, url_for
from sqlalchemy.orm.exc import NoResultFound

from jsonapi_utils.querystring import QueryStringManager as QSManager
from jsonapi_utils.alchemy import sort_query, paginate_query, filter_query
from jsonapi_utils.marshmallow import paginate_result


def jsonapi_list(type_, schema_kls, model, collection, query, endpoint, endpoint_kwargs=None):
    """Helper to get jsonapi result for "get" method on list resource
    Managed concepts:
        - sorting
        - pagination
        - fields restriction
        - filtering
        - jsonapi result structure

    :param str type_: resource type
    :param marshmallow.schema.SchemaMeta schema_kls: a schema class to manage serialization
    :param object model: a Publimodels class
    :param pymongo.collection.Collection collection: a connection to a mongo collection
    :param dict query: a dict containing mongo query params
    :param str endpoint: the endpoint name to create pagination
    :param dict endpoint_kwargs: kwargs for endpoint url creation
    :return dict: the jsonapi result
    """
    item_count = query.count()
    qs = QSManager(request.args)

    if qs.filters:
        query = filter_query(query, qs.filters)

    query = collection.find(query)

    if qs.sorting:
        query = sort_query(query, qs.sorting)

    query = paginate_query(query, qs.pagination)

    items = list(query)

    schema_kwargs = {}
    if qs.fields.get(type_):
        schema_kwargs = {'only': set(schema_kls._declared_fields.keys()) & set(qs.fields[type_])}
        schema_kwargs['only'].add('id')
    schema = schema_kls(many=True, **schema_kwargs)

    result = schema.dump(items)

    if endpoint_kwargs is None:
        endpoint_kwargs = {}
    paginate_result(result.data, item_count, qs, url_for(endpoint, **endpoint_kwargs))

    return result.data


def jsonapi_detail(type_, schema_kls, model, key, value, collection):
    """Helper to get jsonapi result for "get" method on detail resource
    Managed concepts:
        - fields restriction
        - jsonapi result structure

    :param str type_: resource type
    :param marshmallow.schema.SchemaMeta schema_kls: a schema class to manage serialization
    :param object model: a Publimodels class
    :param pymongo.collection.Collection collection: a connection to a mongo collection
    :param str key: the model field to filter on
    :param value: the model field value to filter on
    :return dict: the jsonapi result
    """
    item = collection.find_one({key: value})
    if not item:
        return {'errors': [{'detail': "%s not found" % model.__name__}]}, 404

    qs = QSManager(request.args)

    schema_kwargs = {}
    if qs.fields.get(type_):
        schema_kwargs = {'only': set(schema_kls._declared_fields.keys()) & set(qs.fields[type_])}
        schema_kwargs['only'].add('id')
    schema = schema_kls(**schema_kwargs)

    result = schema.dump(item)

    return result.data
