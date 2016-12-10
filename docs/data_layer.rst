Data layer
==========

A data layer is a CRUD interface between resource methods and data providers or ORMs. The data layer class must
implement the BaseDataLayer class. You can use one of the default:
    - Sqlalchemy
    - Mongodb
data layer or create a custom one that better fit to your needs.

Usage example:

.. code:: python

    from flask_rest_jsonapi import ResourceList, SqlalchemyDataLayer

    from your_project.models import Post
    from your_project.schemas import PostSchema
    from your_project.extensions import sql_db

    def get_base_query(self, **view_kwargs):
        query = self.session.query(Post)


    class PostList(ResourceList):
        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'model': Post, 'session': sql_db.session},
                          'get_base_query': get_base_query}

        resource_type = 'post'
        schema = {'cls': PostSchema}
        endpoint = {'alias': 'post_list'}


Sqlalchemy
----------

A data layer around SQLAlchemy

ResourceList
~~~~~~~~~~~~

Instance attributs:
    - model (Model): an sqlalchemy model
    - session (Session): a sqlalchemy session instance

Class attributs:
    - get_base_query (callable): a callable to retrieve the base data in get method
    - before_create_instance (callable) *Optional*: make additional work before to create an instance in the post method

Example:

.. code:: python

    import datetime

    from sqlalchemy import NoResultFound
    from flask_rest_jsonapi import ResourceList, SqlalchemyDataLayer

    from your_project.models import Post
    from your_project.schemas import PostSchema
    from your_project.extensions import sql_db
    from your_project.lib import get_topic


    def get_base_query(self, **view_kwargs):
        query = self.session.query(Post)


    def before_create_instance(self, data, **view_kwargs):
        """Make additional work before to create your instance:
            - make checks
            - retrieve a related object to plug to the instance
            - compute an instance attribut
            - or what ever you want.
        """
        try:
            topic = self.session.query(Topic).filter_by(topic_id=view_kwargs['topic_id']).one()
        except NoReultFOund:
            abort(404)

        data['topic'] = topic
        data['created_at'] = datetime.datetime.utcnow()


    class PostList(ResourceList):
        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'model': Post, 'session': sql_db.session},
                          'get_base_query': get_base_query,
                          'before_create_instance': before_create_instance}

        resource_type = 'post'
        schema = {'cls': PostSchema}
        endpoint = {'alias': 'post_list'}


ResourceDetail
~~~~~~~~~~~~~~

Instance attributs:
    - model (Model): an sqlalchemy model
    - session (Session): a sqlalchemy session instance
    - id_field (str): the model identifier attribut name
    - url_param_name (str): the name of the url param in route to retrieve value from

Class attributs:
    - before_update_instance (callable) *Optional*: make additional work before to update an instance in the patch method
    - before_delete_instance (callable) *Optional*: make additional work before to delete an instance in the delete method

Example:

.. code:: python

    from sqlalchemy import NoResultFound
    from flask_rest_jsonapi import ResourceList, SqlalchemyDataLayer

    from your_project.models import Post
    from your_project.schemas import PostSchema
    from your_project.extensions import sql_db


    def before_update_instance(self, item, data, **view_kwargs):
        """Make additional work before to update your instance:
            - make checks
            - compute an instance attribut
            - or what ever you want.
        """
        data['updated_at'] = datetime.datetime.utcnow()


    def before_delete_instance(self, data, **view_kwargs):
        """Make additional work before to delete your instance:
            - make checks
            - or what ever you want.
        """


    class PostDetail(ResourceDetail):

        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'session': sql_db.session,
                                     'model': Post,
                                     'id_field': 'post_id',
                                     'url_param_name': 'post_id'},
                          'before_update_instance': before_update_instance,
                          'before_delete_instance': before_delete_instance}

        resource_type = 'post'
        schema = {'cls': PostSchema}

Available opertations
~~~~~~~~~~~~~~~~~~~~

All available operations on sqlalchemy model field (depends on the field type) could be used for filtering. See the
SQLAlchemy documentation to learn more.


Mongo
-----

A data layer around MongoDB

ResourceList
~~~~~~~~~~~~

Instance attributs:
    - collection (str): the mongodb collection name
    - mongo: the mongodb connector
    - model (type): the type of the document

Class attributs:
    - get_base_query (callable): a callable to retrieve the base data in get method

Example:

.. code:: python

    from flask_rest_jsonapi import ResourceList, MongoDataLayer

    from your_project.models import Post
    from your_project.schemas import PostSchema
    from your_project.extensions import mongo


    def get_base_query(self, **view_kwargs):
        """Get base data filter
        """
        return {'topic_id': view_kwargs['topic_id']}


    class PostList(ResourceList):

        class Meta:
            data_layer = {'cls': MongoDataLayer,
                          'kwargs': {'collection': 'logging',
                                     'model': dict,
                                     'mongo': mongo},
                          'get_base_query': get_base_query}

        resource_type = 'post'
        schema = {'cls': PostSchema}
        endpoint = {'alias': 'post_list'}


ResourceDetail
~~~~~~~~~~~~~~

Instance attributs:
    - collection (str): the mongodb collection name
    - mongo: the mongodb connector
    - model (type): the type of the document
    - id_field (str): the model identifier attribut name
    - url_param_name (str): the name of the url param in route to retrieve value from

Example:

.. code:: python

    from flask_rest_jsonapi import ResourceList, MongoDataLayer

    from your_project.models import Post
    from your_project.schemas import PostSchema
    from your_project.extensions import mongo


    class PostDetail(ResourceDetail):

        class Meta:
            data_layer = {'cls': MongoDataLayer,
                          'kwargs': {'collection': 'post',
                                     'mongo': mongo,
                                     'model': dict,
                                     'id_field': 'post_id',
                                     'url_param_name': 'post_id'}}

        resource_type = 'post'
        schema = {'cls': PostSchema}

Available opertations
~~~~~~~~~~~~~~~~~~~~

All available operations on mongodb field (depends on the field type) could be used for filtering. See the MongoDB
documentation to learn more.
