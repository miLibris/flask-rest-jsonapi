# -*- coding: utf-8 -*-

"""Helper to create pagination links according to jsonapi specification"""

from __future__ import division
from six.moves.urllib.parse import urlencode
from math import ceil
from copy import copy

from flask import current_app


def add_pagination_links(data, object_count, querystring, base_url):
    """Add pagination links to result

    :param dict data: the result of the view
    :param int object_count: number of objects in result
    :param QueryStringManager querystring: the managed querystring fields and values
    :param str base_url: the base url for pagination
    """
    links = {}
    all_qs_args = copy(querystring.querystring)

    links['self'] = base_url

    # compute self link
    if all_qs_args:
        links['self'] += '?' + urlencode(all_qs_args)

    if querystring.pagination.get('size') != '0' and object_count > 1:
        # compute last link
        page_size = int(querystring.pagination.get('size', 0)) or current_app.config['PAGE_SIZE']
        last_page = int(ceil(object_count / page_size))

        if last_page > 1:
            links['first'] = links['last'] = base_url

            all_qs_args.pop('page[number]', None)

            # compute first link
            if all_qs_args:
                links['first'] += '?' + urlencode(all_qs_args)

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
