Tutorial
========

In this tutorial, we will cover a simple blog example with topic, post and author entities.

.. Note::
    I don't include imports on this tutorial for readability but you can see them in examples/full_example.py.

.. Note::
    All requests and responses are well formatted for better readability.

Initialize flask application, API and database
----------------------------------------------

.. code:: python

    app = Flask(__name__)
    api = Api(app)
    engine = create_engine('sqlite:////tmp/test.db')
    Session = sessionmaker(bind=engine)
    session = Session()


Define and initialize models
----------------------------

.. code:: python


    Base = declarative_base()
    
    
    class Topic(Base):
        __tablename__ = 'topic'
    
        id = Column(Integer, primary_key=True)
        name = Column(String)
    
    
    class Post(Base):
        __tablename__ = 'post'
    
        id = Column(Integer, primary_key=True)
        title = Column(String)
        content = Column(String)
        topic_id = Column(Integer, ForeignKey('topic.id'))
        author_id = Column(Integer, ForeignKey('author.id'))
    
        topic = relationship("Topic", backref="posts")
        author = relationship("Author", backref="posts")
    
    
    class Author(Base):
        __tablename__ = 'author'
    
        id = Column(Integer, primary_key=True)
        name = Column(String)
    
    Base.metadata.create_all(engine)


Define marshamllow-jsonapi schemas
----------------------------------

.. code:: python

    class TopicSchema(Schema):
    
        class Meta:
            type_ = 'topic'
            self_view = 'topic_detail'
            self_view_kwargs = {'topic_id': '<id>'}
            self_view_many = 'topic_list'
    
        id = fields.Str(dump_only=True)
        name = fields.Str(required=True)
    
        posts = Relationship(related_view='post_list',
                             related_view_kwargs={'topic_id': '<id>'},
                             many=True,
                             type_='post')
    
    
    class PostSchema(Schema):
    
        class Meta:
            type_ = 'post'
            self_view = 'post_detail'
            self_view_kwargs = {'post_id': '<id>'}
    
        id = fields.Str(dump_only=True)
        title = fields.Str(required=True)
        content = fields.Str()
        author_name = fields.Function(lambda obj: obj.author.name)
        author_id = fields.Int(required=True)
    
        topic = Relationship(related_view='topic_detail',
                             related_view_kwargs={'topic_id': '<topic.id>'},
                             type_='topic')
    
        author = Relationship(related_view='author_detail',
                              related_view_kwargs={'author_id': '<author.id>'},
                              type_='author')
    
    
    class AuthorSchema(Schema):
    
        class Meta:
            type_ = 'author'
            self_view = 'author_detail'
            self_view_kwargs = {'author_id': '<id>'}
            self_view_many = 'author_list'
    
        id = fields.Str(dump_only=True)
        name = fields.Str(required=True)
    
        posts = Relationship(related_view='post_list',
                             related_view_kwargs={'author_id': '<id>'},
                             many=True,
                             type_='post')


Register resources and routes
-----------------------------

.. code:: python

    def topic_get_base_query(self, **view_kwargs):
        return self.session.query(Topic)
    
    api.list_route('topic_list',
                   '/topics',
                   resource_type='topic',
                   schema=TopicSchema,
                   data_layer=SqlalchemyDataLayer,
                   data_layer_kwargs={'model': Topic, 'session': session},
                   data_layer_additional_functions={'get_base_query': topic_get_base_query})
    
    api.detail_route('topic_detail',
                     '/topics/<int:topic_id>',
                     resource_type='topic',
                     schema=TopicSchema,
                     data_layer=SqlalchemyDataLayer,
                     data_layer_kwargs={'model': Topic, 'session': session, 'id_field': 'id', 'url_param_name': 'topic_id'})
    
    
    def post_get_base_query(self, **view_kwargs):
        query = self.session.query(Post)
    
        if view_kwargs.get('topic_id'):
            query = query.join(Topic).filter_by(id=view_kwargs['topic_id'])
        elif view_kwargs.get('author_id'):
            query = query.join(Author).filter_by(id=view_kwargs['author_id'])
    
        return query
    
    
    def post_before_create_instance(self, data, **view_kwargs):
        try:
            topic = self.session.query(Topic).filter_by(id=str(view_kwargs['topic_id'])).one()
        except NoResultFound:
            return ErrorFormatter.format_error(['Topic not found']), 404
    
        data['topic'] = topic
    
    api.list_route('post_list',
                   '/topics/<int:topic_id>/posts',
                   '/authors/<int:author_id>/posts',
                   resource_type='post',
                   schema=PostSchema,
                   schema_get_kwargs={'exclude': ('author_id', )},
                   schema_post_kwargs={'exclude': ('author_name', )},
                   data_layer=SqlalchemyDataLayer,
                   data_layer_kwargs={'model': Post, 'session': session},
                   data_layer_additional_functions={'get_base_query': post_get_base_query,
                                                    'before_create_instance': post_before_create_instance},
                   endpoint_include_view_kwargs=True)
    
    api.detail_route('post_detail',
                     '/posts/<int:post_id>',
                     resource_type='post',
                     schema=PostSchema,
                     schema_get_kwargs={'exclude': ('author_id', )},
                     data_layer=SqlalchemyDataLayer,
                     data_layer_kwargs={'model': Post, 'session': session, 'id_field': 'id', 'url_param_name': 'post_id'})
    
    
    def author_get_base_query(self, **view_kwargs):
        return self.session.query(Author)
    
    api.list_route('author_list',
                   '/authors',
                   resource_type='author',
                   schema=AuthorSchema,
                   data_layer=SqlalchemyDataLayer,
                   data_layer_kwargs={'model': Author, 'session': session},
                   data_layer_additional_functions={'get_base_query': author_get_base_query})
    
    api.detail_route('author_detail',
                     '/authors/<int:author_id>',
                     resource_type='author',
                     schema=AuthorSchema,
                     data_layer=SqlalchemyDataLayer,
                     data_layer_kwargs={'model': Author,
                                        'session': session,
                                        'id_field': 'id',
                                        'url_param_name': 'author_id'})
    
If you want to separate resource configuration from routing, you can do something like that:

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


List topics
-----------

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics" -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"

Response::

    {
        "data": [],
        "links": {
            "first": "/topics",
            "last": "/topics",
            "self": "/topics"
        }
    }


Create topic
------------

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics" -X POST\
      -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"\
      -d '{
        "data": {
          "type": "topic",
          "attributes": {
            "name": "topic 1"
          }
        }
      }'

Response::

    {
        "data": {
            "attributes": {
                "name": "topic 1"
            },
            "id": "1",
            "links": {
                "self": "/topics/1"
            },
            "relationships": {
                "posts": {
                    "links": {
                        "related": "/topics/1/posts"
                    }
                }
            },
            "type": "topic"
        },
        "links": {
            "self": "/topics/1"
        }
    }

Now you can list again topics:

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics" -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"

Response::

    {
        "data": [
            {
                "attributes": {
                    "name": "topic 1"
                },
                "id": "1",
                "links": {
                    "self": "/topics/1"
                },
                "relationships": {
                    "posts": {
                        "links": {
                            "related": "/topics/1/posts"
                        }
                    }
                },
                "type": "topic"
            }
        ],
        "links": {
            "first": "/topics",
            "last": "/topics?page%5Bnumber%5D=1",
            "self": "/topics"
        }
    }


Update topic
------------

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics/1" -X PATCH\
      -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"\
      -d '{
        "data": {
          "type": "topic",
          "id": "1",
          "attributes": {
            "name": "topic 1 updated"
          }
        }
      }'

Response::

    {
        "data": {
            "attributes": {
                "name": "topic 1 updated"
            },
            "id": "1",
            "links": {
                "self": "/topics/1"
            },
            "relationships": {
                "posts": {
                    "links": {
                        "related": "/topics/1/posts"
                    }
                }
            },
            "type": "topic"
        },
        "links": {
            "self": "/topics/1"
        }
    }


Delete topic
------------

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics/1" -X DELETE\
      -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"


Create author
-------------

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/authors" -X POST\
      -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"\
      -d '{
        "data": {
          "type": "author",
          "attributes": {
            "name": "John Smith"
          }
        }
      }'

Response::

    {
        "data": {
            "attributes": {
                "name": "John Smith"
            },
            "id": "1",
            "links": {
                "self": "/authors/1"
            },
            "relationships": {
                "posts": {
                    "links": {
                        "related": "/authors/1/posts"
                    }
                }
            },
            "type": "author"
        },
        "links": {
            "self": "/authors/1"
        }
    }


Create post with an author in a topic
-------------------------------------

Before creating a post, we have to create a topic (because we have deleted the only one previously)

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics" -X POST\
      -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"\
      -d '{
        "data": {
          "type": "topic",
          "attributes": {
            "name": "topic 1"
          }
        }
      }'

Response::

    {
        "data": {
            "attributes": {
                "name": "topic 1"
            },
            "id": "1",
            "links": {
                "self": "/topics/1"
            },
            "relationships": {
                "posts": {
                    "links": {
                        "related": "/topics/1/posts"
                    }
                }
            },
            "type": "topic"
        },
        "links": {
            "self": "/topics/1"
        }
    }

Now we have a new topic, so let's create a post for it

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics/1/posts" -X POST\
      -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"\
      -d '{
        "data": {
          "type": "post",
          "attributes": {
            "title": "post 1",
            "content": "content of the post 1",
            "author_id": "1"
          }
        }
      }'

Response::

    {
        "data": {
            "attributes": {
                "author_id": 1,
                "content": "content of the post 1",
                "title": "post 1"
            },
            "id": "1",
            "links": {
                "self": "/posts/1"
            },
            "relationships": {
                "author": {
                    "links": {
                        "related": "/authors/1"
                    }
                },
                "topic": {
                    "links": {
                        "related": "/topics/2"
                    }
                }
            },
            "type": "post"
        },
        "links": {
            "self": "/posts/1"
        }
    }


List posts of topic 1
---------------------

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/topics/1/posts" -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"

Response::

    {
        "data": [
            {
                "attributes": {
                    "author_name": "John Smith",
                    "content": "content of the post 1",
                    "title": "post 1"
                },
                "id": "1",
                "links": {
                    "self": "/posts/1"
                },
                "relationships": {
                    "author": {
                        "links": {
                            "related": "/authors/1"
                        }
                    },
                    "topic": {
                        "links": {
                            "related": "/topics/1"
                        }
                    }
                },
                "type": "post"
            }
        ],
        "links": {
            "first": "/topics/1/posts",
            "last": "/topics/1/posts?page%5Bnumber%5D=1",
            "self": "/topics/1/posts"
        }
    }


List posts of author 1 (John Smith)
-----------------------------------

Request:

.. code:: bash

    $ curl "http://127.0.0.1:5000/authors/1/posts" -H "Content-Type: application/vnd.api+json"\
      -H "Accept: application/vnd.api+json"

Response::

    {
        "data": [
            {
                "attributes": {
                    "author_name": "John Smith",
                    "content": "content of the post 1",
                    "title": "post 1"
                },
                "id": "1",
                "links": {
                    "self": "/posts/1"
                },
                "relationships": {
                    "author": {
                        "links": {
                            "related": "/authors/1"
                        }
                    },
                    "topic": {
                        "links": {
                            "related": "/topics/1"
                        }
                    }
                },
                "type": "post"
            }
        ],
        "links": {
            "first": "/authors/1/posts",
            "last": "/authors/1/posts?page%5Bnumber%5D=1",
            "self": "/authors/1/posts"
        }
    }
