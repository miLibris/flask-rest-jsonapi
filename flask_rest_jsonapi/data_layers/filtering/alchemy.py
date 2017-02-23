# -*- coding: utf-8 -*-

from sqlalchemy import and_, or_

from flask_rest_jsonapi.exceptions import InvalidFilters


def create_filters(model, filter_info):
    """Apply filters from filters information to base query

    :param DeclarativeMeta model: the model of the node
    :param dict filter_info: current node filter information
    """
    filters = []
    for filter_ in filter_info:
        filters.append(Node(model, filter_).resolve())

    return filters


class Node(object):

    def __init__(self, model, filter_):
        self.model = model
        self.filter_ = filter_

    def resolve(self):
        if 'or' not in self.filter_ and 'and' not in self.filter_:
            if self.val is None and self.field is None:
                raise InvalidFilters("Can't find value of field in a filter")

            value = None

            if isinstance(self.val, dict):
                related_model = self.get_related_model(self.name)
                value = Node(related_model, self.val).resolve()

            if '__' in self.name:
                column = self.get_column(self.model, self.name.split('__')[0])
                operator = self.get_operator(column, self.op)
                value = self.get_value(self.model, self.field, self.val)
                value = {self.name.split('__')[1]: value}
            else:
                column = self.get_column(self.model, self.name)
                operator = self.get_operator(column, self.op)
                if value is None:
                    value = self.get_value(self.model, self.field, self.val)

            if isinstance(value, dict):
                return getattr(column, operator)(**value)
            else:
                return getattr(column, operator)(value)

        if 'or' in self.filter_:
            return or_(Node(self.model, filt).resolve() for filt in self.filter_['or'])
        if 'and' in self.filter_:
            return and_(Node(self.model, filt).resolve() for filt in self.filter_['and'])

    @property
    def name(self):
        """Return the name of the node or raise a BadRequest exception

        :return str: the name of the field to filter on
        """
        try:
            return self.filter_['name']
        except KeyError:
            raise InvalidFilters("Can't find name of a filter")

    @property
    def op(self):
        """Return the operator of the node

        :return str: the operator to use in the filter
        """
        try:
            return self.filter_['op']
        except KeyError:
            raise InvalidFilters("Can't find op of a filter")

    @property
    def val(self):
        """Return the val of the node

        :return: the value to filter with
        """
        return self.filter_.get('val')

    @property
    def field(self):
        """Return the field of the node

        :return: the field to pick up value from to filter with
        """
        return self.filter_.get('field')

    @staticmethod
    def get_column(model, field):
        """Get the column object

        :param DeclarativeMeta model: the model
        :param str field: the field
        :return InstrumentedAttribute: the column to filter on
        """
        try:
            return getattr(model, field)
        except AttributeError:
            raise InvalidFilters("%s has no attribute %s in a filter" % (model.__name__, field))

    @staticmethod
    def get_operator(column, operator):
        """Get the function operator from his name

        :return callable: a callable to make operation on a column
        """
        operators = (operator, operator + '_', '__' + operator + '__')

        for op in operators:
            if hasattr(column, op):
                return op

        raise InvalidFilters("%s has no operator %s in a filter" % (column.key, op))

    @staticmethod
    def get_value(model, field, value):
        """Get the value to filter on

        :return: the value to filter on
        """
        if field is not None:
            try:
                return getattr(model, field)
            except AttributeError:
                raise InvalidFilters("%s has no attribute %s in a filter" % (model.__name__, field))

        return value

    def get_related_model(self, relationship_field):
        """Get the related model of a relationship field

        :param str relationship_field: the relationship field
        :return DeclarativeMeta: the related model
        """
        return getattr(self.model, relationship_field).property.mapper.class_
