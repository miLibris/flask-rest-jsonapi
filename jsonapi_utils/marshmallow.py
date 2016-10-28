# -*- coding: utf-8 -*-

from urllib.parse import urlencode
from math import ceil
from copy import copy

from jsonapi_utils.constants import DEFAULT_PAGE_SIZE


def paginate_result(data, object_count, querystring, base_url):
    """Add pagination links to result

    Args:
        data (dict): the result of the view
        object_count (int): number of main objects in result
    """
    links = {}
    all_qs_args = copy(querystring.querystring)

    links['self'] = links['first'] = links['last'] = base_url

    # compute self link
    if all_qs_args:
        links['self'] += '?' + urlencode(all_qs_args)

    try:
        del all_qs_args['page[number]']
    except KeyError:
        pass

    # compute first link
    if all_qs_args:
        links['first'] += '?' + urlencode(all_qs_args)

    # compute last link
    page_size = int(querystring.pagination.get('size', 0)) or DEFAULT_PAGE_SIZE
    last_page = int(ceil(object_count / page_size))
    all_qs_args.update({'page[number]': last_page})
    links['last'] += '?' + urlencode(all_qs_args)

    # compute previous and next link
    current_page = int(querystring.pagination.get('number', 0)) or 1
    if current_page > 1:
        all_qs_args.update({'page[number]': current_page - 1})
        links['prev'] = '?'.join((base_url, urlencode(all_qs_args)))
    if current_page < last_page:
        all_qs_args.update({'page[number]': current_page + 1})
        links['next'] = '?'.join((base_url, urlencode(all_qs_args)))

    data['links'] = links
