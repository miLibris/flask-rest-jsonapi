# -*- coding: utf-8 -*-

from sqlalchemy.sql.expression import desc, asc, text

from jsonapi_utils.constants import DEFAULT_PAGE_SIZE


def paginate_query(query, paginate_info):
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


def sort_query(query, sort_info):
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


def filter_query(query, filter_info, model):
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
            raise Exception("field: %s not found on model: %s" % (item['field'], model.__name__))
        if item['op'] == 'in':
            filt = column.in_(item['value'].split(','))
        else:
            try:
                attr = next(filter(lambda e: hasattr(column, e % item['op']), ['%s', '%s_', '__%s__'])) % item['op']
            except IndexError:
                raise Exception("Invalid filter operator for field: %s" % (item['field']))
            if item['value'] == 'null':
                item['value'] = None
            filt = getattr(column, attr)(item['value'])
            query = query.filter(filt)

    return query
