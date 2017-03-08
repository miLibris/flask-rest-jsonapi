# -*- coding: utf-8 -*-

from sqlalchemy import and_, or_, not_

from flask_rest_jsonapi.exceptions import InvalidFilters
from flask_rest_jsonapi.schema import get_relationships


def create_filters(model, filter_info, resource):
    """Apply filters from filters information to base query

    :param DeclarativeMeta model: the model of the node
    :param dict filter_info: current node filter information
    :param Resource resource: the resource
    """
    filters = []
    for filter_ in filter_info:
        filters.append(Node(model, filter_, resource.opts, resource.schema).resolve())

    return filters


class Node(object):

    def __init__(self, model, filter_, opts, schema):
        self.model = model
        self.filter_ = filter_
        self.opts = opts
        self.schema = schema

    def resolve(self):
        if 'or' not in self.filter_ and 'and' not in self.filter_:
            if self.val is None and self.field is None:
                raise InvalidFilters("Can't find value or field in a filter")

            value = self.value

            if isinstance(self.val, dict):
                value = Node(self.related_model, self.val, self.opts, self.related_schema).resolve()

            if '__' in self.filter_.get('name', ''):
                value = self.value
                value = {self.filter_['name'].split('__')[1]: value}

            if isinstance(value, dict):
                return getattr(self.column, self.operator)(**value)
            else:
                return getattr(self.column, self.operator)(value)

        if 'or' in self.filter_:
            return or_(Node(self.model, filt, self.opts, self.schema).resolve() for filt in self.filter_['or'])
        if 'and' in self.filter_:
            return and_(Node(self.model, filt, self.opts, self.schema).resolve() for filt in self.filter_['and'])
        if 'not' in self.filter_:
            return not_(Node(self.model, self.filter_['not'], self.opts, self.schema).resolve())

    @property
    def name(self):
        """Return the name of the node or raise a BadRequest exception

        :return str: the name of the field to filter on
        """
        name = self.filter_.get('name')

        if name is None:
            raise InvalidFilters("Can't find name of a filter")

        if '__' in name:
            name = name.split('__')[0]

        if name not in self.schema._declared_fields:
            raise InvalidFilters("{} has no attribut {}".format(self.schema.__name__, name))

        return name

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

    @property
    def column(self):
        """Get the column object

        :param DeclarativeMeta model: the model
        :param str field: the field
        :return InstrumentedAttribute: the column to filter on
        """
        field = self.name

        if self.schema._declared_fields[field].attribute is not None:
            field = self.schema._declared_fields[field].attribute

        try:
            return getattr(self.model, field)
        except AttributeError:
            raise InvalidFilters("{} has no attribute {} in a filter".format(self.model.__name__, field))

    @property
    def operator(self):
        """Get the function operator from his name

        :return callable: a callable to make operation on a column
        """
        operators = (self.op, self.op + '_', '__' + self.op + '__')

        for op in operators:
            if hasattr(self.column, op):
                return op

        raise InvalidFilters("{} has no operator {} in a filter".format(self.column.key, self.op))

    @property
    def value(self):
        """Get the value to filter on

        :return: the value to filter on
        """
        if self.field is not None:
            try:
                return getattr(self.model, self.field)
            except AttributeError:
                raise InvalidFilters("{} has no attribute {} in a filter".format(self.model.__name__, self.field))

        return self.val

    @property
    def related_model(self):
        """Get the related model of a relationship field

        :return DeclarativeMeta: the related model
        """
        relationship_field = self.name

        if relationship_field not in get_relationships(self.schema):
            raise InvalidFilters("{} has no relationship attribut {}".format(self.schema.__name__, relationship_field))

        if hasattr(self.opts, 'schema_to_model') and self.opts.schema_to_model.get(relationship_field) is not None:
            relationship_field = self.opts.schema_to_model[relationship_field]

        return getattr(self.model, relationship_field).property.mapper.class_

    @property
    def related_schema(self):
        """Get the related schema of a relationship field

        :return Schema: the related schema
        """
        relationship_field = self.name

        if relationship_field not in get_relationships(self.schema):
            raise InvalidFilters("{} has no relationship attribut {}".format(self.schema.__name__, relationship_field))

        return self.schema._declared_fields[relationship_field].schema.__class__
