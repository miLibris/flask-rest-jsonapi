# -*- coding: utf-8 -*-

from marshmallow import class_registry
from marshmallow.base import SchemaABC
from marshmallow_jsonapi.fields import Relationship as MarshmallowJsonapiRelationship

from flask_rest_jsonapi.exceptions import InvalidField, InvalidInclude


def compute_schema(schema_cls, default_kwargs, qs, include):
    """Compute a schema around compound documents and sparse fieldsets

    :param Schema schema_cls: the schema class
    :param dict default_kwargs: the schema default kwargs
    :param QueryStringManager qs: qs
    :param list include: the relation field to include data from

    :return Schema schema: the schema computed
    """
    # manage include_data parameter of the schema
    schema_kwargs = default_kwargs
    schema_kwargs['include_data'] = tuple()

    if include:
        for include_path in include:
            field = include_path.split('.')[0]
            if field not in schema_cls._declared_fields:
                raise InvalidInclude(field, "%s has no attribut %s" % (schema_cls.__name__, field))
            elif not issubclass(schema_cls._declared_fields[field].__class__, MarshmallowJsonapiRelationship):
                raise InvalidInclude(field, "%s is not a relationship attribut of %s" % (field, schema_cls.__name__))
            schema_kwargs['include_data'] += (field, )

    # create base schema instance
    schema = schema_cls(**schema_kwargs)

    # manage sparse fieldsets
    if schema.opts.type_ in qs.fields:
        # check that sparse fieldsets exists in the schema
        for field in qs.fields[schema.opts.type_]:
            if field not in schema.declared_fields:
                raise InvalidField(field, "%s has no attribut %s" % (schema.__class__.__name__, field))

        tmp_only = set(schema.declared_fields.keys()) & set(qs.fields[schema.opts.type_])
        if schema.only:
            tmp_only &= set(schema.only)
        schema.only = tuple(tmp_only)

    # make sure id field is in only parameter unless marshamllow will raise an Exception
    if schema.only and 'id' not in schema.only:
        schema.only += ('id',)

    # manage compound documents
    if include:
        for include_path in include:
            field = include_path.split('.')[0]
            relation_field = schema.declared_fields[field]
            related_schema_cls = schema.declared_fields[field].__dict__['_Relationship__schema']
            related_schema_kwargs = {}
            if isinstance(related_schema_cls, SchemaABC):
                related_schema_kwargs['many'] = related_schema_cls.many
                related_schema_cls = related_schema_cls.__class__
            if isinstance(related_schema_cls, str):
                related_schema_cls = class_registry.get_class(related_schema_cls)
            if '.' in include_path:
                related_include = ['.'.join(include_path.split('.')[1:])]
            else:
                related_include = None
            related_schema = compute_schema(related_schema_cls, related_schema_kwargs, qs, related_include)
            relation_field.__dict__['_Relationship__schema'] = related_schema

    return schema
