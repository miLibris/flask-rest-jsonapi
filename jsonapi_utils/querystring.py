class QueryStringManager(object):
    """Querystring parser for JSONAPI

    :param dict query_string: query string dict from flask to use
    """

    MANAGED_KEYS = (
        'filter',
        'page',
        'fields',
        'sort',
        'include'
    )

    def __init__(self, query_string):
        if not isinstance(query_string, dict):
            raise ValueError('QueryStringManager require a dict-like object query_string parameter')

        self.query = query_string

    def _get_key_values(self, index, multiple_values=True):
        """Return a dict containing key / values items for a given key, used for items like filters, page, etc.

        :param str index: index to use for filtering
        :param bool multiple_values: indicate if each key can have more than one value
        :return: a dict of key / values items
        """
        results = {}
        for key, value in self.query.items():
            if not key.startswith(index):
                continue
            key_start = key.index('[') + 1
            key_end = key.index(']')
            item_key = key[key_start:key_end]
            if multiple_values:
                item_value = value.split(',')
            else:
                item_value = value
            results.update({item_key: item_value})
        return results

    @property
    def querystring(self):
        """Return original querystring but containing only managed keys
        """
        ret = {}
        for key, value in self.query.items():
            if key.startswith(self.MANAGED_KEYS):
                ret[key] = value
        return ret

    @property
    def filters(self):
        """Return filters from query string.

        Filters will be parsed based on jsonapi recommendations_

        .. _recommendations: http://jsonapi.org/recommendations/#filtering

        Return value will be a dict containing all fields by resource, for example::

            {
                "user": [1, 2],
                "articles": [12]
            }
        """
        return self._get_key_values('filter')

    @property
    def pagination(self):
        """Return all page parameters as a dict.

        To allow multiples strategies, all parameters starting with `page` will be included. e.g::

            {
                "number": '25',
                "size": '150',
                "offset": '250',
                "limit": '150'
            }

            Example with number strategy::

                >>> query_string = {'page[number]': '25', 'page[size]': '10'}
                >>> parsed_query.pagination
                {'number': '25', 'size': '10'}

            Example with offset / limit strategy::

                >>> query_string = {'page[offset]': '100', 'page[limit]': '100'}
                >>> parsed_query.pagination
                {'offset': '100', 'limit': '100'}

        """
        # check values type
        result = self._get_key_values('page', multiple_values=False)
        for key, value in result.items():
            try:
                int(value)
            except ValueError:
                raise Exception("Invalid value for %s attribut of page in querystring" % key)

        return result

    @property
    def fields(self):
        """Return fields wanted by client.

        Return value will be a dict containing all fields by resource, for example::

            {
                "user": ['name', 'email'],
                "articles": ['title', 'short_description']
            }
        """
        return self._get_key_values('fields')

    @property
    def sorting(self):
        """Return fields to sort by including sort name for SQLAlchemy and row
        sort parameter for other ORMs

        Example of return value::
            [
                {'field': 'created_at', 'order': 'desc', 'raw': '-created_at'},
                {'field': 'number', 'order': 'asc', 'raw': 'number'},
                {'field': 'author.number', 'order': 'asc', 'raw': 'author.number'}
            ]
        """
        sort_fields = self.query.get('sort')
        if not sort_fields:
            return []
        sorting_results = []
        for sort_field in sort_fields.split(','):
            field = sort_field.replace('-', '')
            order = 'desc' if sort_field.startswith('-') else 'asc'
            sorting_results.append({'field': field, 'order': order, 'raw': sort_field})
        return sorting_results

    @property
    def include(self):
        """Return fields to include
        """
        include_param = self.query.get('include')
        return include_param.split(',') if include_param else []
