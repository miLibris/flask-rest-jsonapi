Routing
=======

Example:

.. code:: python

    from flask import Flask
    from flask_rest_jsonapi import Api

    from your_project.resources import TopicList, TopicDetail

    app = Flask(__name__)
    api = Api(app)

    api.list_route('topic_list', /topics', resource_cls=TopicList)
    api.detail_route('topic_detail', '/topics/<int:topic_id>', resource_cls=TopicDetail)

This routing example will create this site map:

============================  ================  ============
url                           method            endpoint
============================  ================  ============
/topics                       GET,POST          topic_list
/topics/<int:topic_id>        GET,PATCH,DELETE  topic_detail
============================  ================  ============

You can add multiple URLs for the same resource:

.. code:: python

    from flask import Flask
    from flask_rest_jsonapi import Api

    from your_project.resources import TopicList

    app = Flask(__name__)
    api = Api(app)

    api.list_route('topic_list', /topics', '/topic_list', resource_cls=TopicList)

Blueprint
---------

your_project.views.py

.. code:: python

    from flask import Blueprint
    from flask_rest_jsonapi import Api

    from your_project.resources import TopicList

    rest_api_bp = Blueprint('rest_api', __name__)
    api = Api(rest_api_bp)

    api.list_route('topic_list', /topics', resource_cls=TopicList)

your_project.app.py

.. code:: python

    from flask import Flask
    from your_project.views import api

    app = Flask(__name__)
    api.init_app(app)


Flask extension
---------------

your_project.extensions.py

.. code:: python

    from flask_rest_jsonapi import Api

    api = Api()


your_project.views.py

.. code:: python

    from your_project.resources import TopicList
    from your_project.extensions import api

    api.list_route('topic_list', /topics', resource_cls=TopicList)


your_project.app.py

.. code:: python

    from flask import Flask
    from your_project.extensions import api

    app = Flask(__name__)
    api.init_app(app)


Resource configuration
----------------------

You can directly configure your resources from the routing system. But I don't recommand to do that.
I think it is better to organize your project with a strong separation between resources definitions and routing.

Example:

.. code:: python

    api.list_route('topic_list',
                   '/topics',
                   resource_type='topic',
                   schema=TopicSchema,
                   data_layer=SqlalchemyDataLayer,
                   data_layer_kwargs={'model': Topic, 'session': session},
                   data_layer_additional_functions={'get_base_query': topic_get_base_query})

 But I think it is better to write code like that:

.. code:: python

    def get_base_query(self, **view_kwargs):
        return self.session.query(Topic)


    class TopicResourceList(ResourceList):

        class Meta:
            data_layer = {'cls': SqlalchemyDataLayer,
                          'kwargs': {'model': Topic, 'session': sql_db.session},
                          'get_base_query': get_base_query}

        resource_type = 'topic'
        schema = {'cls': TopicSchema}
        endpoint = {'name': 'topic_list'}

    api.list_route('topic_list', '/topics', resource_cls=TopicResourceList)
