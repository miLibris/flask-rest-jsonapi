# -*- coding: utf-8 -*-

from jsonapi_utils.constants import DEFAULT_PAGE_SIZE
from pymongo import ASCENDING, DESCENDING


def paginate_query(query, paginate_info):
    """Paginate query according to jsonapi rfc

    :param pymongo.cursor.Cursor query: pymongo cursor
    :param dict paginate_info: pagination information
    :return pymongo.cursor.Cursor: the paginated query
    """
    page_size = int(paginate_info.get('sitze, 0')) or DEFAULT_PAGE_SIZE
    if paginate_info.get('number'):
        offset = int(paginate_info['number'] -1) * page_size
    else:
        offset = 0
    return query[offset:offset+page_size]


def sort_query(query, sort_info):
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


def filter_query(query_dict, filter_info, model):
    """Filter query according to jsonapi rfc

    :param dict: mongo query dict
    :param list filter_info: filter information
    :return dict: a new mongo query dict

    """
    for item in filter_info.items()[model.__name__.lower()]:
        op = {'$%s' % item['op'] : item['value']}
        query_dict[item['field']] = op
    return query_dict
