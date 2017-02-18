# -*- coding: utf-8 -*-

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.sql.expression import desc, asc, text

from flask_rest_jsonapi.constants import DEFAULT_PAGE_SIZE
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.exceptions import ObjectNotFound, RelationNotFound, RelatedObjectNotFound


class SqlalchemyDataLayer(BaseDataLayer):

    def __init__(self, *args, **kwargs):
        super(SqlalchemyDataLayer, self).__init__(*args, **kwargs)

        if not hasattr(self, 'session'):
            raise Exception("You must provide a session in data_layer_kwargs to use sqlalchemy data layer in %s"
                            % self.resource.__name__)
        if not hasattr(self, 'model'):
            raise Exception("You must provide a model in data_layer_kwargs to use sqlalchemy data layer in %s"
                            % self.resource.__name__)

    def create_object(self, data, **view_kwargs):
        """Create an object through sqlalchemy

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object from sqlalchemy
        """
        self.before_create_object(data, **view_kwargs)

        obj = self.model(**data)

        self.session.add(obj)
        self.session.commit()

        return obj

    def get_object(self, **view_kwargs):
        """Retrieve an object through sqlalchemy

        :params dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an object from sqlalchemy
        """
        if not hasattr(self, 'url_field'):
            raise Exception("You must provide an url_field in data_layer_kwargs in %s" % self.resource.__name__)

        id_field = getattr(self, 'id_field', 'id')
        try:
            filter_field = getattr(self.model, id_field)
        except Exception:
            raise Exception("Unable to find attribut: %s on model: %s" % (id_field, self.model.__name__))

        filter_value = view_kwargs[self.url_field]

        try:
            obj = self.session.query(self.model).filter(filter_field == filter_value).one()
        except NoResultFound:
            raise ObjectNotFound('.'.join([self.model.__name__, id_field]),
                                 "Could not find %s.%s=%s object" % (self.model.__name__, id_field, filter_value))

        return obj

    def get_collection(self, qs, **view_kwargs):
        """Retrieve a collection of objects through sqlalchemy

        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the number of object and the list of objects
        """
        query = self.query(**view_kwargs)

        if qs.filters:
            query = self.filter_query(query, qs.filters, self.model)

        if qs.sorting:
            query = self.sort_query(query, qs.sorting)

        object_count = query.count()

        query = self.paginate_query(query, qs.pagination)

        return object_count, query.all()

    def update_object(self, obj, data, **view_kwargs):
        """Update an object through sqlalchemy

        :param DeclarativeMeta obj: an object from sqlalchemy
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        self.before_update_object(obj, data, **view_kwargs)

        for field in data:
            if hasattr(obj, field):
                setattr(obj, field, data[field])

        self.session.commit()

    def delete_object(self, obj, **view_kwargs):
        """Delete an object through sqlalchemy

        :param DeclarativeMeta item: an item from sqlalchemy
        :param dict view_kwargs: kwargs from the resource view
        """
        self.before_delete_object(obj, **view_kwargs)

        self.session.delete(obj)
        self.session.commit()

    def create_relation(self, json_data, related_id_field, **view_kwargs):
        """Create a relation

        :param dict json_data: the request params
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        """
        obj = self.get_object(**view_kwargs)

        if not hasattr(obj, self.relation_field):
            raise RelationNotFound

        related_model = getattr(obj.__class__, self.relation_field).property.mapper.class_

        for obj_ in json_data['data']:
            related_object = self.get_related_object(related_model, related_id_field, obj_)
            getattr(obj, self.relation_field).append(related_object)

        self.session.commit()

    def get_relation(self, related_type_, related_id_field, **view_kwargs):
        """Get a relation

        :param str related_type_: the related resource type
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        :return tuple: the object and related object(s)
        """
        obj = self.get_object(**view_kwargs)

        if not hasattr(obj, self.relation_field):
            raise RelationNotFound(self.relation_field,
                                   "%s as no attribut %s" % (self.model.__name__, self.relation_field))

        related_objects = getattr(obj, self.relation_field)

        if related_objects is None:
            return obj, related_objects

        if isinstance(related_objects, InstrumentedList):
            return obj,\
                [{'type': related_type_, 'id': getattr(obj_, related_id_field)} for obj_ in related_objects]
        else:
            return obj, {'type': related_type_, 'id': getattr(related_objects, related_id_field)}

    def update_relation(self, json_data, related_id_field, **view_kwargs):
        """Update a relation

        :param dict json_data: the request params
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        """
        obj = self.get_object(**view_kwargs)

        if not hasattr(obj, self.relation_field):
            raise RelationNotFound

        related_model = getattr(obj.__class__, self.relation_field).property.mapper.class_

        if not isinstance(json_data['data'], list):
            related_object = None

            if json_data['data'] is not None:
                related_object = self.get_related_object(related_model, related_id_field, json_data['data'])

            setattr(obj, self.relation_field, related_object)
        else:
            related_objects = []

            for obj_ in json_data['data']:
                related_object = self.get_related_object(related_model, related_id_field, obj_)

            setattr(obj, self.relation_field, related_objects)

        self.session.commit()

    def delete_relation(self, json_data, related_id_field, **view_kwargs):
        """Delete a relation

        :param dict json_data: the request params
        :param str related_id_field: the identifier field of the related model
        :param dict view_kwargs: kwargs from the resource view
        """
        obj = self.get_object(**view_kwargs)

        if not hasattr(obj, self.relation_field):
            raise RelationNotFound

        related_model = getattr(obj.__class__, self.relation_field).property.mapper.class_

        for obj_ in json_data['data']:
            related_object = self.get_related_object(related_model, related_id_field, obj_)
            getattr(obj, self.relation_field).remove(related_object)

        self.session.commit()

    def get_related_object(self, related_model, related_id_field, obj):
        """Get a related object

        :param Model related_model: an sqlalchemy model
        :param str related_id_field: the identifier field of the related model
        :param DeclarativeMeta obj: the sqlalchemy object to retrieve related objects from
        :return DeclarativeMeta: a related object
        """
        try:
            related_object = self.session.query(related_model)\
                                         .filter(getattr(related_model, related_id_field) == obj['id'])\
                                         .one()
        except NoResultFound:
            raise RelatedObjectNotFound('%s.%s' % (related_model.__name__, related_id_field),
                                        "Could not find %s.%s=%s object" % (related_model.__name__,
                                                                            related_id_field,
                                                                            obj['id']))

        return related_object

    def filter_query(self, query, filter_info, model):
        """Filter query according to jsonapi 1.0

        :param Query query: sqlalchemy query to sort
        :param list filter_info: filter information
        :param DeclarativeMeta model: an sqlalchemy model
        :return Query: the sorted query
        """
        for obj in filter_info[model.__name__.lower()]:
            try:
                column = getattr(model, obj['field'])
            except AttributeError:
                continue
            if obj['op'] == 'in':
                filt = column.in_(obj['value'].split(','))
            else:
                try:
                    attr = next(iter(filter(lambda e: hasattr(column, e % obj['op']),
                                            ['%s', '%s_', '__%s__']))) % obj['op']
                except IndexError:
                    continue
                if obj['value'] == 'null':
                    obj['value'] = None
                filt = getattr(column, attr)(obj['value'])
                query = query.filter(filt)

        return query

    def sort_query(self, query, sort_info):
        """Sort query according to jsonapi 1.0

        :param Query query: sqlalchemy query to sort
        :param list sort_info: sort information
        :return Query: the sorted query
        """
        expressions = {'asc': asc, 'desc': desc}
        order_objects = []
        for sort_opt in sort_info:
            field = text(sort_opt['field'])
            order = expressions.get(sort_opt['order'])
            order_objects.append(order(field))
        return query.order_by(*order_objects)

    def paginate_query(self, query, paginate_info):
        """Paginate query according to jsonapi 1.0

        :param Query query: sqlalchemy queryset
        :param dict paginate_info: pagination information
        :return Query: the paginated query
        """
        if int(paginate_info.get('size', 1)) == 0:
            return query

        page_size = int(paginate_info.get('size', 0)) or DEFAULT_PAGE_SIZE
        query = query.limit(page_size)
        if paginate_info.get('number'):
            query = query.offset((int(paginate_info['number']) - 1) * page_size)

        return query

    def query(self, **view_kwargs):
        """Construct the base query to retrieve wanted data

        :param dict view_kwargs: kwargs from the resource view
        """
        return self.session.query(self.model)

    def before_create_object(self, data, **view_kwargs):
        """Provide additional data before object creation

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        pass

    def before_update_object(self, obj, data, **view_kwargs):
        """Make checks or provide additional data before update object

        :param obj: an object from data layer
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        pass

    def before_delete_object(self, obj, **view_kwargs):
        """Make checks before delete object

        :param obj: an object from data layer
        :param dict view_kwargs: kwargs from the resource view
        """
        pass
