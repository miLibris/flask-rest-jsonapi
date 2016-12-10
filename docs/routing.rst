Routing
=======

The routing system is the default flask MethodView one.

Example:

.. code:: python

    from flask import Flask

    from your_project.resources import TopicList, TopicDetail,\
        PostList, PostDetail

    app = Flask(__name__)

    app.add_url_rule('/topics',
                     view_func=TopicList.as_view('topic_list'))
    app.add_url_rule('/topics/<int:topic_id>',
                     view_func=TopicDetail.as_view('topic_detail'))

    app.add_url_rule('/topics/<int:topic_id>/posts',
                     view_func=PostList.as_view('post_list'))
    app.add_url_rule('/posts/<int:post_id>',
                     view_func=PostDetail.as_view('post_detail'))

This routing example will create this site map::

    ============================  ================  ============
    url                           method            endpoint
    ============================  ================  ============
    /topics                       GET,POST          topic_list
    /topics/<int:topic_id>        GET,PATCH,DELETE  topic_detail
    /topics/<int:topic_id>/posts  GET,POST          post_list
    /posts/<int:post_id>          GET,PATCH,DELETE  post_detail
    ============================  ================  ============

You can add mulitple url for the same resource like that:

.. code:: python

    from flask import Flask

    from your_project.resources import TopicList

    app = Flask(__name__)

    topic_list_view = TopicList.as_view('topic_list')

    app.add_url_rule('/topics',
                     view_func=topic_list_view)

    app.add_url_rule('/topic_list',
                     view_func=topic_list_view)
