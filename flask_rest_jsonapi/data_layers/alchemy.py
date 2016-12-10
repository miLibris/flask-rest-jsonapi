# -*- coding: utf-8 -*-

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc, asc, text

from flask_rest_jsonapi.constants import DEFAULT_PAGE_SIZE
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.exceptions import EntityNotFound


class SqlalchemyDataLayer(BaseDataLayer):

    def __init__(self, *args, **kwargs):
        super(SqlalchemyDataLayer, self).__init__(*args, **kwargs)

        if not hasattr(self, 'session'):
            raise Exception("You must provide a session to use sqlalchemy data layer")
        if not hasattr(self, 'model'):
            raise Exception("You must provide a model to use sqlalchemy data layer")

    def get_item(self, **view_kwargs):
        """Retrieve an item through sqlalchemy

        :params dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an item from sqlalchemy
        """
        if not hasattr(self, 'id_field'):
            raise Exception("You must provide an id_field in data layer kwargs in %s" % self.resource_cls.__name__)
        if not hasattr(self, 'url_param_name'):
            raise Exception("You must provide an url_param_name in data layer kwargs in %s"
                            % self.resource_cls.__name__)

        try:
            filter_field = getattr(self.model, self.id_field)
        except Exception:
            raise Exception("Unable to find column name: %s on model: %s" % (self.id_field, self.model.__name__))

        filter_value = view_kwargs[self.url_param_name]

        try:
            item = self.session.query(self.model).filter(filter_field == filter_value).one()
        except NoResultFound:
            raise EntityNotFound(self.model.__name__, filter_value)

        return item

    def get_items(self, qs, **view_kwargs):
        """Retrieve a collection of items

        :param QueryStringManager qs: a querystring manager to retrieve information from url
        :param dict view_kwargs: kwargs from the resource view
        :return int item_count: the number of items in the collection
        :return list query.all(): the list of items
        """
        if not hasattr(self, 'get_base_query'):
            raise Exception("You must provide an get_base_query in data layer kwargs in %s"
                            % self.resource_cls.__name__)

        query = self.get_base_query(**view_kwargs)

        if qs.filters:
            query = self.filter_query(query, qs.filters, self.model)

        if qs.sorting:
            query = self.sort_query(query, qs.sorting)

        item_count = query.count()

        query = self.paginate_query(query, qs.pagination)

        return item_count, query.all()

    def create_and_save_item(self, data, **view_kwargs):
        """Create and save an item through sqlalchemy

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an item from sqlalchemy
        """
        self.before_create_instance(data, **view_kwargs)

        item = self.model(**data)

        self.session.add(item)
        self.session.commit()

        return item

    def update_and_save_item(self, item, data, **view_kwargs):
        """Update an instance of an item and store changes

        :param DeclarativeMeta item: an item from sqlalchemy
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        self.before_update_instance(item, data, **view_kwargs)

        for field in data:
            if hasattr(item, field):
                setattr(item, field, data[field])

        self.session.commit()

    def delete_item(self, item, **view_kwargs):
        """Delete an item

        :param DeclarativeMeta item: an item from sqlalchemy
        :param dict view_kwargs: kwargs from the resource view
        """
        self.before_delete_instance(item, **view_kwargs)

        self.session.delete(item)
        self.session.commit()

    def filter_query(self, query, filter_info, model):
        """Filter query according to jsonapi rfc

        :param Query query: sqlalchemy query to sort
        :param list filter_info: filter information
        :param DeclarativeMeta model: an sqlalchemy model
        :return Query: the sorted query
        """
        for item in filter_info[model.__name__.lower()]:
            try:
                column = getattr(model, item['field'])
            except AttributeError:
                continue
            if item['op'] == 'in':
                filt = column.in_(item['value'].split(','))
            else:
                try:
                    attr = next(iter(filter(lambda e: hasattr(column, e % item['op']),
                                            ['%s', '%s_', '__%s__']))) % item['op']
                except IndexError:
                    continue
                if item['value'] == 'null':
                    item['value'] = None
                filt = getattr(column, attr)(item['value'])
                query = query.filter(filt)

        return query

    def sort_query(self, query, sort_info):
        """Sort query according to jsonapi rfc

        :param Query query: sqlalchemy query to sort
        :param list sort_info: sort information
        :return Query: the sorted query
        """
        expressions = {'asc': asc, 'desc': desc}
        order_items = []
        for sort_opt in sort_info:
            field = text(sort_opt['field'])
            order = expressions.get(sort_opt['order'])
            order_items.append(order(field))
        return query.order_by(*order_items)

    def paginate_query(self, query, paginate_info):
        """Paginate query according to jsonapi rfc

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

    def get_base_query(self, **view_kwargs):
        """Construct the base query to retrieve wanted data

        :param dict view_kwargs: kwargs from the resource view
        """
        raise NotImplemented

    def before_create_instance(self, data, **view_kwargs):
        """Provide additional data before instance creation

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        pass

    def before_update_instance(self, item, data, **view_kwargs):
        """Make checks or provide additional data before update instance

        :param DeclarativeMeta item: an item from sqlalchemy
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        pass

    def before_delete_instance(self, item, **view_kwargs):
        """Make checks before delete instance

        :param DeclarativeMeta item: an item from sqlalchemy
        :param dict view_kwargs: kwargs from the resource view
        """
        pass

    @classmethod
    def configure(cls, data_layer):
        """Plug get_base_query and optionally before_create_instance to the instance class

        :param dict data_layer: information from Meta class used to configure the data layer instance
        """
        if data_layer.get('get_base_query') is not None and callable(data_layer['get_base_query']):
            cls.get_base_query = data_layer['get_base_query']

        if data_layer.get('before_create_instance') is not None and callable(data_layer['before_create_instance']):
            cls.before_create_instance = data_layer['before_create_instance']

        if data_layer.get('before_update_instance') is not None and callable(data_layer['before_update_instance']):
            cls.before_update_instance = data_layer['before_update_instance']

        if data_layer.get('before_delete_instance') is not None and callable(data_layer['before_delete_instance']):
            cls.before_delete_instance = data_layer['before_delete_instance']
