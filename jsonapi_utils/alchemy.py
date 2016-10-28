# -*- coding: utf-8 -*-

from sqlalchemy.sql.expression import desc, asc, text

from jsonapi_utils.constants import DEFAULT_PAGE_SIZE


def paginate_query(query, pagination_kwargs):
    """Paginate query result according to jsonapi rfc

    :param sqlalchemy.orm.query.Query query: sqlalchemy queryset
    :param dict pagination_kwargs: pagination informations
    """
    page_size = int(pagination_kwargs.get('size', 0)) or DEFAULT_PAGE_SIZE
    query = query.limit(page_size)
    if pagination_kwargs.get('number'):
        query = query.offset((int(pagination_kwargs['number']) - 1) * page_size)

    return query


def sort_query(query, querystring):
    """
    :param query: sqlalchemy query to sort
    :param JSONAPIQueryString querystring: current querystring
    """
    expressions = {'asc': asc, 'desc': desc}
    order_items = []
    for sort_opt in querystring.sorting:
        field = text(sort_opt['field'])
        order = expressions.get(sort_opt['order'])
        order_items.append(order(field))
    return query.order_by(*order_items)
