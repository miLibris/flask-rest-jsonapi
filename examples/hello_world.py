# -*- coding: utf-8 -*-

from flask import Flask
from flask_rest_jsonapi import Api, ResourceDetail

app = Flask(__name__)
api = Api(app)


class HelloWorld(ResourceDetail):
    def get(self):
        return "Hello world"

api.detail_route('index', '/', resource_cls=HelloWorld)

if __name__ == '__main__':
    app.run(debug=True)
