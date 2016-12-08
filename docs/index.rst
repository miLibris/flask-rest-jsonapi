.. jsonapi-utils documentation master file, created by
   sphinx-quickstart on Fri Oct 21 14:33:15 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to flask-rest-jsonapi documentation!
============================================

flask-rest-jsonapi is an implementation of jsonapi reference http://jsonapi.org with flask and marshmallow.
You can interface any data provider like SQLAlchemy or MongoDB (already available) or create your custom data layer.

I have created this library because i was looking for the best way to implement rest api. The jsonapi specification is
a very strong specification about interactions between the api and the caller and i think it is a very good one.

There are already lot of very good rest library based on flask like Flask-restfull or Flask-restless, and i would like
to create an helper library as flexible as Flask-restfull (https://github.com/flask-restful/flask-restful) and as simple
and fast to use as Flask-restless (https://github.com/jfinkels/flask-restless).

Moreover you can use any data provider instead of other flask rest api library that only allow to you to use SQLAlchemy.
You can use SQLAlchemy or MongoDB or create you own custom data layer to interact with the data provider of your choice.

Here is a quick example:

.. code:: python

    from flask import Flask
    from flask_rest_jsonapi import ResourceDetail

    app = Flask(__name__)

    class HelloWorld(ResourceDetail):
        def get(self):
            return "Hello world"

    app.add_url_rule('/', view_func=HelloWorld.as_view('index'))

    if __name__ == '__main__':
        app.run(debug=True)

Save this file as api.py

Launch local server:

.. code:: bash

    $ python api.py
     * Running on http://127.0.0.1:5000/
     * Restarting with reloader


Now you can try this:

.. code:: bash

    $ curl http://127.0.0.1:5000/
    Hello world

Contents
--------

.. toctree::
   :maxdepth: 2
   :glob:

   install
   resource
   data_layer
   sorting
   filtering
   pagination
   full_example



Api reference
-------------

* :ref:`genindex`
* :ref:`modindex`
