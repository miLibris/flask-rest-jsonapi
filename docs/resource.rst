Resource
========

Flask-Rest-JSONAPI provides 2 resource class helpers:

    - ResourceList
    - ResourceDetail

.. Note::
    If you forget to set one of the required attributes of a resource class, the library will raise an Exception to
    help you find which attribute is missing in which resource class.


ResourceList
------------

This class provides a default implementation of GET and POST methods to:

    - GET: retrieve a list of items with the GET request method
    - POST: create an item with POST request method

You can rewrite those methods if the default behaviour is not enough for you.

If you want to use one of those default method implementations, you have to configure your resource class.

Class attributes:

    - resource_type (str): name of the resource type

    - schema (dict): schema information: 

        - cls (Schema): a marshmallow schema class
        - get_kwargs (dict) *Optional*: additional kwargs for instance schema in get method
        - post_kwargs (dict) *Optional*: additional kwargs for instance schema in post method

    - endpoint (dict): endpoint information:

        - name (str): name of the endpoint
        - include_view_kwargs (boolean) *Optional*: set it to True if you want to include view kwargs to the endpoint
          url build context

    - Meta (class):

        - data_layer (dict): data layer information:

            - cls (BaseDataLayer): a data layer class like SqlalchemyDataLayer, MongoDataLayer or your custom data layer

        - get_decorators (list) *Optional*: a list of decorators to plug to the get method
        - post_decorators (list) *Optional*: a list of decorators to plug to the post method
        - disabled_methods (list) *Optional*: a list of request methods to disallow access to. Those methods will return a
          405 (Method Not Allowed) status code

Example:

.. code:: python

    from flask_rest_jsonapi import ResourceList, SqlalchemyDataLayer

    from your_project.models import Post
    from your_project.schemas import PostSchema
    from your_project.extensions import sql_db, oauth2

    def get_base_query(self, **view_kwargs):
        query = self.session.query(Post)


    class PostList(ResourceList):
        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'model': Post, 'session': sql_db.session},
                          'get_base_query': get_base_query}

            get_decorators = [oauth2.require_oauth('post_list')]
            post_decorators = [oauth2.require_oauth('post_create')]

        resource_type = 'post'
        schema = {'cls': PostSchema,
                  'get_kwargs': {'only': ('title', 'content', 'created')},
                  'post_kwargs': {'only': ('title', 'content')}}
        endpoint = {'name': 'post_list',
                    'include_view_kwargs': True}


ResourceDetail
--------------

This class provides a default implementation of GET, PATCH and DELETE methods to:

    - GET: retrieve item details with the GET request method
    - POST: update an item with the PATCH request method
    - DELETE: delete an item with the DELETE request method

You can rewrite those methods if the default behaviour is not enough for you.

If you want to use one of those default method implementations, you have to configure your resource class.

Class attributes:

    - resource_type (str): name of the resource type

    - schema (dict): schema information: 

        - cls (Schema): a Marshmallow schema class
        - get_kwargs (dict) *Optional*: additional kwargs for instance schema in get method
        - patch_kwargs (dict) *Optional*: additional kwargs for instance schema in patch method

    - Meta (class):

        - data_layer (dict): data layer information:

            - cls (BaseDataLayer): a data layer class like SqlalchemyDataLayer, MongoDataLayer or your custom data layer

        - get_decorators (list) *Optional*: a list of decorators to plug to the get method
        - post_decorators (list) *Optional*: a list of decorators to plug to the post method
        - disabled_methods (list) *Optional*: a list of request methods to disallow acces to. Those methods will return a
          405 (Method Not Allowed) status code

Example:

.. code:: python

    from flask_rest_jsonapi import ResourceList, SqlalchemyDataLayer

    from your_project.models import Post
    from your_project.schemas import PostSchema
    from your_project.extensions import sql_db

    class PostDetail(ResourceDetail):

        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'session': sql_db.session,
                                     'model': Post,
                                     'id_field': 'post_id',
                                     'url_param_name': 'post_id'}}

            get_decorators = [oauth2.require_oauth('provider_detail')]
            patch_decorators = [oauth2.require_oauth('provider_update')]

            disabled_methods = ['DELETE']

        resource_type = 'provider'
        schema = {'cls': ProviderSchema,
                  'get_kwargs': {'only': ('title', 'content', 'created', 'author')},
                  'patch_kwargs': {'only': ('title', 'content')}}


Method rewrite
--------------

If you want to rewrite the default implementation of a resource method you can
return a tuple instead of flask BaseReponse, like in Flask-RESTful.

Example:

.. code:: python

    from flask import Flask
    from flask_rest_jsonapi import ResourceDetail

    app = Flask(__name__)


    class HelloWorld(ResourceDetail):
        def get(self):
            return "Hello world", 202, {'custom_header':'custom_header_value'}

Keep in mind that if you want to stay compliant with jsonapi specifications you have to return well formatted json
responses and status code. For example if you rewrite the POST method to distribute the creation of an item you have to
return a 202 (Accepted) status code.
