# -*- coding: utf-8 -*-

from marshmallow_jsonapi import Schema, fields


def test_list_nested_field():
    class PostSchema(Schema):
        class Meta:
            type_ = 'posts'

        id = fields.Integer(as_string=True, dump_only=True)
        tags = fields.List(fields.Str())

    schema = PostSchema()
    result = schema.dump({
        'id': 1,
        'tags': ['foo', 'bar']
    })
    assert result['data']['attributes']['tags'][0] == 'foo'
    assert result['data']['attributes']['tags'][1] == 'bar'
