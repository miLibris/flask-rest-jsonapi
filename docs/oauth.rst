.. _oauth:

OAuth
=====

.. currentmodule:: flask_rest_jsonapi

Flask-REST-JSONAPI supports OAuth via `Flask-OAuthlib <https://github.com/lepture/flask-oauthlib>`_

Example:

.. code-block:: python

    from flask import Flask
    from flask_rest_jsonapi import Api
    from flask_oauthlib.provider import OAuth2Provider

    app = Flask(__name__)
    oauth2 = OAuth2Provider()

    api = Api()
    api.init_app(app)
    api.oauth_manager(oauth2)


In this example Flask-REST-JSONAPI will protect all your resource methods with this decorator ::

    oauth2.require_oauth(<scope>)

The pattern of the scope is ::

    <action>_<resource_type>

Where action is:

* list: for the get method of a ResourceList
* create: for the post method of a ResourceList
* get: for the get method of a ResourceDetail
* update: for the patch method of a ResourceDetail
* delete: for the delete method of a ResourceDetail

Example ::

    list_person

If you want to customize the scope you can provide a function that computes your custom scope. The function has to look like this:

.. code-block:: python

    def get_scope(resource, method):
            """Compute the name of the scope for oauth

            :param Resource resource: the resource manager
            :param str method: an http method
            :return str: the name of the scope
            """
            return 'custom_scope'

Usage example:

.. code-block:: python

    from flask import Flask
    from flask_rest_jsonapi import Api
    from flask_oauthlib.provider import OAuth2Provider

    app = Flask(__name__)
    oauth2 = OAuth2Provider()

    api = Api()
    api.init_app(app)
    api.oauth_manager(oauth2)
    api.scope_setter(get_scope)

.. note::

    You can name the custom scope computation method as you want but you have to set the two required parameters "resource" and "method" as in this previous example.

If you want to disable OAuth or create custom method protection for a resource you can add this option to the resource manager.

Example:

.. code-block:: python

    from flask_rest_jsonapi import ResourceList
    from your_project.extensions import oauth2

    class PersonList(ResourceList):
        disable_oauth = True

        @oauth2.require_oauth('custom_scope')
        def get(*args, **kwargs):
            return 'Hello world !'
