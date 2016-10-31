# jsonapi-utils
Python utils to help you build a jsonapi http://jsonapi.org/

# Build rest api easily

## Stack

- oauthlib
- flask_restful
- marshmallow_jsonapi
- sqlalchemy

## Managed concepts:

- jsonapi result structure
- pagination
- sort
- fields limitation

## Exemple

```python
# -*- coding: utf-8 -*-

from flask_restful import Resource
from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields
from jsonapi_utils.helpers import jsonapi_list, jsonapi_detail
from models import Post

from application.extensions import oauth2, sql_db


class PostSchema(Schema):

    class Meta:
        type_ = 'post'
        self_view = 'post_detail'
        self_view_kwargs = {'post_id': '<id>'}
        self_view_many = 'post_list'

    id = fields.Str(dump_only=True)
    title = fields.Str()
    content = fields.Str()

    comments = Relationship(related_view='comment_list',
                            related_view_kwargs={'post_id': '<id>'},
                            many=True,
                            type_='comments')


class PostList(Resource):

    @oauth2.require_oauth('post_list')
    def get(self):
        """Get list of posts
        """
        query = sql_db.session.query(Post)

        return jsonapi_list('post', PostSchema, query, 'post_list')


class PostDetail(Resource):

    @oauth2.require_oauth('post_detail')
    def get(self, post_id):
        """Get post details
        """
        return jsonapi_detail('post', PostSchema, Post, 'id', post_id, sql_db.session)
```