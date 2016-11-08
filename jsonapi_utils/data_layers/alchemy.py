# -*- coding: utf-8 -*-

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import desc, asc, text

from jsonapi_utils.constants import DEFAULT_PAGE_SIZE


class SqlalchemyDataLayer(object):

    def __init__(self, **kwargs):
        if kwargs.get('session_factory') is not None:
            self.session = kwargs['session_factory'].session
        self.kwargs = kwargs

    def get_item(self, **kwargs):
        """
        """
        try:
            filter_field = getattr(self.kwargs['model'], self.kwargs['id_field'])
        except Exception:
            raise Exception("Unable to find column name: %s on model: %s"
                            % (self.kwargs['id_field'], self.kwargs['model'].__name__))

        filter_value = str(kwargs[self.kwargs['url_param_name']])

        try:
            item = self.session.query(self.kwargs['model']).filter(filter_field == filter_value).one()
        except NoResultFound:
            raise Exception("%s not found" % self.kwargs['model'].__name__)

        return item

    def persiste_update(self):
        """
        """
        self.session.commit()

    def get_items(self, resource_list_instance, qs, **kwargs):
        """
        """
        query = getattr(resource_list_instance, 'get_base_query')(self.session, **kwargs)

        if qs.filters:
            query = self.filter_query(query, qs.filters, self.kwargs['model'])

        if qs.sorting:
            query = self.sort_query(query, qs.sorting)

        item_count = query.count()

        query = self.paginate_query(query, qs.pagination)

        return item_count, query.all()

    def filter_query(self, query, filter_info, model):
        """Filter query according to jsonapi rfc

        :param sqlalchemy.orm.query.Query query: sqlalchemy query to sort
        :param list filter_info: filter informations
        :return sqlalchemy.orm.query.Query: the sorted query
        :param sqlalchemy.ext.declarative.api.DeclarativeMeta model: an sqlalchemy model
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

        :param sqlalchemy.orm.query.Query query: sqlalchemy query to sort
        :param list sort_info: sort informations
        :return sqlalchemy.orm.query.Query: the sorted query
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

        :param sqlalchemy.orm.query.Query query: sqlalchemy queryset
        :param dict paginate_info: pagination informations
        :return sqlalchemy.orm.query.Query: the paginated query
        """
        page_size = int(paginate_info.get('size', 0)) or DEFAULT_PAGE_SIZE
        query = query.limit(page_size)
        if paginate_info.get('number'):
            query = query.offset((int(paginate_info['number']) - 1) * page_size)

        return query

    def create_and_save_item(self, data, before_create_instance, **kwargs):
        """
        """
        before_create_instance(self.session, data, **kwargs)

        item = self.kwargs['model'](**data)

        self.session.add(item)
        self.session.commit()

        return item
