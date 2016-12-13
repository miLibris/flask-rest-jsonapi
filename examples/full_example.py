# -*- coding: utf-8 -*-

from flask import Flask
from flask_rest_jsonapi import Api, SqlalchemyDataLayer, ErrorFormatter
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields

# Flask application, api and database configuration
app = Flask(__name__)
api = Api(app)
engine = create_engine('sqlite:////tmp/test.db')
Session = sessionmaker(bind=engine)
session = Session()

# Create models
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

# Create tables in db
Base.metadata.create_all(engine)


# Create schemas
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


# Register routes and create resources
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


if __name__ == '__main__':
    app.run(debug=True)
