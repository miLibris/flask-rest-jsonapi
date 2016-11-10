[![Build Status](https://travis-ci.org/miLibris/jsonapi-utils.svg?branch=master)](https://travis-ci.org/miLibris/jsonapi-utils)
[![Coverage Status](https://coveralls.io/repos/github/miLibris/jsonapi-utils/badge.svg)](https://coveralls.io/github/miLibris/jsonapi-utils)

# jsonapi-utils
Python utils to help you build easily a restfull api according to jsonapi reference. http://jsonapi.org/

## Stack

- flask_restful
- marshmallow_jsonapi
- sqlalchemy
- mongodb (coming soon)

## Querystring options

### Managed concepts

- fields restrictions
- pagination
- sorting
- filtering


### Fields restriction
You can restrict fields returned by the view with url querystring parameter "fields".

This dicrease the amount of data transfered and can avoid additional queries to retrieve relationships for example.
It only restrict fields returned for the current resource type not for related entities.

*note: this "id" field is returned in all case so you don't have to specify this field*

Example: ?fields[post]=title,content

In this case you avoid to make additional queries to create related comments links.


### Pagination
*note: You have to implement the pagination feature in your data layer too*

You can add pagination informations with the url querystring parameter "page".
You can specify the page number with "number" and the page size with "size".

Example: ?page[number]=4&page[size]=10

*note: default page size is 20*

Pagination structure in view result (not url encoded for readability):
```json
"links": {
    "self": "/post?page[number]=4&page[size]=10",
    "next": "/post?page[number]=5&page[size]=10",
    "previous": "/post?page[number]=3&page[size]=10"
    "first": "/post?&page[size]=10",
    "last": "/post?page[number]=20&page[size]=10",
}
```
*note: pagination management keeps managed querystring parameters in link generation in order to keep your filter, fields retrieve restrictions, sorting or other querystring parameters during navigation.*


### Sorting
*note: You have to implement the pagination feature in your data layer too*

You can sort result with url querystring parameter "sort".

Example: ?sort=-created,title


### Filtering
*note: You have to implement the pagination feature in your data layer too*

You can filter list view result with url querystring parameter "filter".

The structure of the value for this parameter like this: '[{"field":<field_name>,"op":<operator>,"value":<value>},...]'.

This structure is not a json object but is parsable by json.loads because it is easier to parse than a json object.

Example (not url encoded for readability): ?filter[post]=[{"field":"created","op":"gt","value":"2016-11-10"}]


## Data layer

The data layer is the interface between resources views and data. It could be sqlalchemy, mongodb etc.
If you want to add a new data layer this will be better to inherit it from BaseDataLayer to avoid missing methods and create bugs.

#### Sqlalchemy exemple

```python
# -*- coding: utf-8 -*-

from jsonapi_utils.resource import ResourceDetail, ResourceList
from jsonapi_utils.errors import ErrorFormatter

from your_project.models import Post
from your_project.extensions import oauth2, sql_db
from your_project.schemas.post import PostSchema


def get_base_query(self, **view_kwargs):
    """Build the base query to retrieve the collection of items. Used by the get view of a list resource: the get collection view.

    You can do what ever you want in this function, for example build a complex query to retrieve your data or make checks.
    This function will be dynamically plugged to the data layer and used as the base data collector to retrieve list of items.
    This function is required unless you will receive an NotImplemented Exception.

    :param BaseDataLayer self: the current instance of the data layer
    :param dict view_kwargs: kwargs from the resource view
    :return Query: the query to retrieve the collection of items
    """
    return self.session.query(Post)


def before_create_instance(self, data, **view_kwargs):
    """Update kwargs that will be used to create the new item. Used by the post view of a detail resource: the create item view.

    If you want to make extra work before to create the new item instance you can do this in this function.
    This function will be dynamically plugged to the data layer and used before item instance creation.
    This function is optional if you want to create the new item without extra data.

    :param dict data: the data validated by marshmallow_jsonapi. This dict will be used as kwargs to create the new item.
    :param dict view_kwargs: kwargs from the resource view
    """
    data['extra_attribute'] = 'extra_data'


class PostList(ResourceList):

    class Meta:
        # configure your data layer here
        data_layer = {'name': 'sqlalchemy',
                      'kwargs': {'model': Post, 'session_factory': sql_db},
                      'get_base_query': get_base_query,
                      'before_create_instance': before_create_instance}

        # add additional decorators to the list and create views for example for oauth security
        get_decorators = [oauth2.require_oauth('post_list')]
        post_decorators = [oauth2.require_oauth('post_create')]

    # configure your resource
    resource_type = 'post'
    schema_cls = PostSchema
    collection_endpoint = 'post_list' # used to create self and relationship links
    collection_endpoint_request_view_args = True # used to add the view kwargs to the context of the url links creation


class PostDetail(ResourceDetail):

    class Meta:
        data_layer = {'name': 'sqlalchemy',
                      'kwargs': {'session_factory': sql_db,
                                 'model': Post,
                                 'id_field': 'id', # the model attribute you want to filter on when you retrieve an item
                                 'url_param_name':  'post_id'}} # the name of the key in view kwargs to retrieve the item value you want to filter with

        get_decorators = [oauth2.require_oauth('post_detail')]
        patch_decorators = [oauth2.require_oauth('post_update')]

    resource_type = 'post'
    schema_cls = PostSchema
```