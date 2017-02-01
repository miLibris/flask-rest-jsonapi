# -*- coding: utf-8 -*-

from flask_rest_jsonapi.constants import DEFAULT_PAGE_SIZE
from flask_rest_jsonapi.data_layers.base import BaseDataLayer
from flask_rest_jsonapi.exceptions import ObjectNotFound
from pymongo import ASCENDING, DESCENDING


class MongoDataLayer(BaseDataLayer):

    def __init__(self, **kwargs):
        super(MongoDataLayer, self).__init__(**kwargs)
        if not hasattr(self, 'mongo') or self.mongo is None:
            raise Exception('You must provide a mongo connection')
        if not hasattr(self, 'collection') or self.collection is None:
            raise Exception('You must provide a collection to query')
        if not hasattr(self, 'model') or self.model is None:
            raise Exception('You must provide a proper model class !')

    def get_item(self, **view_kwargs):
        """Retrieve a single item from mongodb.

        :params dict view_kwargs: kwargs from the resource view
        :return dict: a mongo document
        """
        query = self.get_single_item_query(**view_kwargs)
        result = self.get_collection().find_one(query)
        if result is None:
            raise ObjectNotFound(self.collection, view_kwargs.get(self.url_param_name))
        return result

    def get_items(self, qs, **view_kwargs):
        query = self.get_base_query(**view_kwargs)
        if qs.filters:
            query = self.filter_query(query, qs.filters, self.model)
        query = self.get_collection().find(query)
        if qs.sorting:
            query = self.sort_query(query, qs.sorting)
        item_count = query.count()
        query = self.paginate_query(query, qs.pagination)

        return item_count, list(query)

    def create_and_save_item(self, data, **view_kwargs):
        """Create and save a mongo document.

        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        :return object: A publimodels object
        """
        self.before_create_instance(data, **view_kwargs)
        item = self.model(**data)
        self.get_collection().save(item)
        return item

    def update_and_save_item(self, item, data, **view_kwargs):
        """Update an instance of an item and store changes

        :param item: a doucment from mongodb
        :param dict data: the data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        self.before_update_instance(item, data)

        for field in data:
            if hasattr(item, field):
                setattr(item, field, data[field])

        id_query = self.get_single_item_query(**view_kwargs)
        self.get_collection().update(id_query, item)

    def get_collection(self):
        collection = getattr(self.mongo.db, self.collection, None)
        if collection is None:
            raise Exception(
                'Collection %s does not exist' % self.collection
            )
        return collection

    def get_single_item_query(self, **view_kwargs):
        return {self.id_field: view_kwargs.get(self.url_param_name)}

    def filter_query(self, query, filter_info, model):
        """Filter query according to jsonapi rfc

        :param dict: mongo query dict
        :param list filter_info: filter information
        :return dict: a new mongo query dict

        """
        for item in filter_info.items()[model.__name__.lower()]:
            op = {'$%s' % item['op']: item['value']}
            query[item['field']] = op
        return query

    def paginate_query(self, query, paginate_info):
        """Paginate query according to jsonapi rfc

        :param pymongo.cursor.Cursor query: pymongo cursor
        :param dict paginate_info: pagination information
        :return pymongo.cursor.Cursor: the paginated query
        """
        page_size = int(paginate_info.get('size', 0)) or DEFAULT_PAGE_SIZE
        if paginate_info.get('number'):
            offset = (int(paginate_info['number']) - 1) * page_size
        else:
            offset = 0
        return query[offset:offset+page_size]

    def sort_query(self, query, sort_info):
        """Sort query according to jsonapi rfc

        :param pymongo.cursor.Cursor query: pymongo cursor
        :param list sort_info: sort information
        :return pymongo.cursor.Cursor: the paginated query
        """
        expressions = {'asc': ASCENDING, 'desc': DESCENDING}
        for sort_opt in sort_info:
            field = sort_opt['field']
            order = expressions.get(sort_opt['order'])
            query = query.sort(field, order)
        return query

    def before_create_instance(self, data, **view_kwargs):
        """Hook called at object creation.

        :param dict data: data validated by marshmallow
        :param dict view_kwargs: kwargs from the resource view
        """
        pass

    def before_update_instance(self, item, data):
        """Hook called at object update.

        :param item: a document from sqlalchemy
        :param dict data: the data validated by marshmallow
        """
        pass

    def get_base_query(self, **view_kwargs):
        """Construct the base query to retrieve wanted data.
        This would be created through metaclass.

        :param dict view_kwargs: Kwargs from the resource view
        """
        raise NotImplemented

    @classmethod
    def configure(cls, data_layer):
        """Plug get_base_query to the instance class.

        :param dict data_layer: information from Meta class used to configure
        the data layer
        """
        if data_layer.get('get_base_query') is not None and callable(data_layer['get_base_query']):
            cls.get_base_query = data_layer['get_base_query']
