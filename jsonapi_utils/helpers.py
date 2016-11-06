# -*- coding: utf-8 -*-

from flask import request, url_for
from sqlalchemy.orm.exc import NoResultFound
from marshmallow import ValidationError
from marshmallow_jsonapi.exceptions import IncorrectTypeError

from jsonapi_utils.querystring import QueryStringManager as QSManager
from jsonapi_utils.alchemy import sort_query, paginate_query, filter_query
from jsonapi_utils.marshmallow import paginate_result


def jsonapi_list(type_, schema_kls, model, query, endpoint, endpoint_kwargs=None):
    """Helper to get jsonapi result for "get" method on list resource
    Managed concepts:
        - sorting
        - pagination
        - fields restriction
        - filtering
        - jsonapi result structure

    :param str tyoe_: resource type
    :param marshmallow.schema.SchemaMeta schema_kls: a schema class to manage serialization
    :param sqlalchemy.ext.declarative.api.DeclarativeMeta model: an sqlalchemy model
    :param sqlalchemy.orm.query.Query query: the sqlalchemy data provider
    :param str endpoint: the endpoint name to create pagination
    :param dict endpoint_kwargs: kwargs for endpoint url creation
    :return dict: the jsonapi result
    """
    item_count = query.count()

    qs = QSManager(request.args)

    if qs.filters:
        query = filter_query(query, qs.filters, model)

    if qs.sorting:
        query = sort_query(query, qs.sorting)

    query = paginate_query(query, qs.pagination)

    items = query.all()

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


def jsonapi_detail(type_, schema_kls, model, key, value, sql_db_session):
    """Helper to get jsonapi result for "get" method on detail resource
    Managed concepts:
        - fields restriction
        - jsonapi result structure

    :param str tyoe_: resource type
    :param marshmallow.schema.SchemaMeta schema_kls: a schema class to manage serialization
    :param sqlalchemy.ext.declarative.api.DeclarativeMeta model: an sqlalchemy model
    :param str key: the model field to filter on
    :param value: the model field value to filter on
    :param sqlalchemy.orm.scoping.scoped_session sql_db_session: an sqlalchmy session
    :return dict: the jsonapi result
    """
    try:
        item = sql_db_session.query(model).filter(getattr(model, key) == value).one()
    except NoResultFound:
        return {'errors': [{'detail': "%s not found" % model.__name__}]}, 404

    qs = QSManager(request.args)

    schema_kwargs = {}
    if qs.fields.get(type_):
        schema_kwargs = {'only': set(schema_kls._declared_fields.keys()) & set(qs.fields[type_])}
        schema_kwargs['only'].add('id')
    schema = schema_kls(**schema_kwargs)

    result = schema.dump(item)

    return result.data


def jsonapi_update(schema_kls, model, key, value, sql_db_session):
    """Helper to update a resource

    :param marshmallow.schema.SchemaMeta schema_kls: a schema class to manage serialization
    :param sqlalchemy.ext.declarative.api.DeclarativeMeta model: an sqlalchemy model
    :param str key: the model field to filter on
    :param value: the model field value to filter on
    :param sqlalchemy.orm.scoping.scoped_session sql_db_session: an sqlalchmy session
    :return tuple: result message and status code
    """
    json_data = request.get_json()

    schema = schema_kls(partial=True)
    try:
        data, errors = schema.load(json_data)
    except ValidationError as err:
        return err.messages, 422
    except IncorrectTypeError as err:
        return err.messages, 409

    try:
        if json_data['data']['id'] is None:
            raise KeyError
    except KeyError:
        return {'errors': [{'detail': 'You must provide id of the entity'}]}, 422

    try:
        item = sql_db_session.query(model).filter_by(getattr(model, key) == value).one()
    except NoResultFound:
        return {'errors': [{'detail': 'Entity not found'}]}, 404

    for field in schema.declared_fields.keys():
        if data.get(field):
            setattr(getattr(item, field), data[field])

    sql_db_session.commit()

    return '', 204


def jsonapi_create(schema_kls, model, sql_db_session, before_create_instance):
    """Helper to create a resource

    :param marshmallow.schema.SchemaMeta schema_kls: a schema class to manage serialization
    :param sqlalchemy.ext.declarative.api.DeclarativeMeta model: an sqlalchemy model
    :param sqlalchemy.orm.scoping.scoped_session sql_db_session: an sqlalchmy session
    :param function before_create_instance: a function executed before instance create. You can add additional data for
                                            the new object or make several checks
    :return tuple: result message and status code
    """
    json_data = request.get_json()

    schema = schema_kls()
    try:
        data, errors = schema.load(json_data)
    except ValidationError as err:
        return err.messages, 422
    except IncorrectTypeError as err:
        return err.messages, 409

    before_create_instance(data, sql_db_session)

    item = model(**data)

    sql_db_session.add(item)
    sql_db_session.commit()

    if json_data['data'].get('id') is not None:
        return '', 204
    else:
        return schema.dump(item).data
