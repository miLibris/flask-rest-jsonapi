# -*- coding: utf-8 -*-

from flask import request, url_for
from sqlalchemy.orm.exc import NoResultFound

from jsonapi_utils.querystring import QueryStringManager as QSManager
from jsonapi_utils.alchemy import sort_query, paginate_query
from jsonapi_utils.marshmallow import paginate_result


def jsonapi_list(type_, schema_kls, query, endpoint, endpoint_kwargs=None):
    """
    """
    item_count = query.count()

    qs = QSManager(request.args)

    if qs.sorting:
        query = sort_query(query, qs)

    query = paginate_query(query, qs.pagination)

    items = query.all()

    schema_kwargs = {}
    if qs.fields.get(type_):
        schema_kwargs = {'only': set(schema_kls._declared_fields.keys()) & set(qs.fields[type_])}
    schema = schema_kls(many=True, **schema_kwargs)

    result = schema.dump(items)

    if endpoint_kwargs is None:
        endpoint_kwargs = {}
    paginate_result(result.data, item_count, qs, url_for(endpoint, **endpoint_kwargs))

    return result.data


def jsonapi_detail(type_, schema_kls, model, key, value, sql_db_session):
    """
    """
    try:
        item = sql_db_session.query(model).filter_by(getattr(model, key) == value).one()
    except NoResultFound:
        return {'errors': [{'detail': "%s not found" % model.__class__.__name__}]}, 404

    qs = QSManager(request.args)

    schema_kwargs = {}
    if qs.fields.get(type_):
        schema_kwargs = {'only': set(schema_kls._declared_fields.keys()) & set(qs.fields[type_])}
    schema = schema_kls(many=True, **schema_kwargs)

    result = schema.dump(item)

    return result.data
