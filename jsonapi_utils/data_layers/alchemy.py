# -*- coding: utf-8 -*-

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc, asc, text

from jsonapi_utils.constants import DEFAULT_PAGE_SIZE
from jsonapi_utils.data_layers.base import BaseDataLayer
from jsonapi_utils.exceptions import EntityNotFound


class SqlalchemyDataLayer(BaseDataLayer):

    def __init__(self, **kwargs):
        super(SqlalchemyDataLayer, self).__init__(**kwargs)
        if not hasattr(self, 'session') or self.session is None:
            raise Exception("You must provide de session")

    def get_item(self, **view_kwargs):
        """Retrieve an item through sqlalchemy

        :params dict view_kwargs: kwargs from the resource view
        :return DeclarativeMeta: an item from sqlalchemy
        """
        try:
            filter_field = getattr(self.model, self.id_field)
        except Exception:
            raise Exception("Unable to find column name: %s on model: %s" % (self.id_field, self.model.__name__))

        filter_value = str(view_kwargs[self.url_param_name])

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
        self.before_update_instance(item, data)

        for field in data:
            if hasattr(item, field):
                setattr(item, field, data[field])

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
                    attr = next(filter(lambda e: hasattr(column, e % item['op']), ['%s', '%s_', '__%s__'])) % item['op']
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

    def before_update_instance(self, item, data):
        """Provide additional data before instance creation

        :param DeclarativeMeta item: an item from sqlalchemy
        :param dict data: the data validated by marshmallow
        """
        pass

    @classmethod
    def configure(cls, data_layer):
        """Plug get_base_query and optionally before_create_instance to the instance class

        :param dict data_layer: information from Meta class used to configure the data layer instance
        """
        if data_layer.get('get_base_query') is None or not callable(data_layer['get_base_query']):
            raise Exception("You must provide a get_base_query function with self as first parameter")

        cls.get_base_query = data_layer['get_base_query']

        if data_layer.get('before_create_instance') is not None and callable(data_layer['before_create_instance']):
            cls.before_create_instance = data_layer['before_create_instance']
