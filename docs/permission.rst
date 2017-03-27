.. _permission:

Permission
==========

.. currentmodule:: flask_rest_jsonapi

Flask-REST-JSONAPI provides a very agnostic permission system.

Example:

.. code-block:: python

    from flask import Flask
    from flask_rest_jsonapi import Api
    from your_project.permission import permission_manager

    app = Flask(__name__)

    api = Api()
    api.init_app(app)
    api.permission_manager(permission_manager)

In this previous example, the API will check permission before each method call with the permission_manager function.

The permission manager must be a function that looks like this:

.. code-block:: python

    def permission_manager(view, view_args, view_kwargs, *args, **kwargs):
        """The function use to check permissions

        :param callable view: the view
        :param list view_args: view args
        :param dict view_kwargs: view kwargs
        :param list args: decorator args
        :param dict kwargs: decorator kwargs
        """

.. note::

    Flask-REST-JSONAPI use a decorator to check permission for each method named has_permission. You can provide args and kwargs to this decorators so you can retrieve this args and kwargs in the permission_manager. The default usage of the permission system does not provides any args or kwargs to the decorator.

If permission is denied I recommand to raise exception like that:

.. code-block:: python

    raise JsonApiException(<error_source>,
                           <error_details>,
                           title='Permission denied',
                           status='403')

You can disable the permission system or make custom permission checking management of a resource like that:

.. code-block:: python

    from flask_rest_jsonapi import ResourceList
    from your_project.extensions import api

    class PersonList(ResourceList):
        disable_permission = True

        @api.has_permission('custom_arg', custom_kwargs='custom_kwargs')
        def get(*args, **kwargs):
            return 'Hello world !'

.. warning::

    If you want to use both permission system and oauth support to retrieve information like user from oauth (request.oauth.user) in the permission system you have to initialize permission system before to initialize oauth support because of decorators cascading.

Example:

.. code-block:: python

    from flask import Flask
    from flask_rest_jsonapi import Api
    from flask_oauthlib.provider import OAuth2Provider
    from your_project.permission import permission_manager

    app = Flask(__name__)
    oauth2 = OAuth2Provider()

    api = Api()
    api.init_app(app)
    api.permission_manager(permission_manager) # initialize permission system first
    api.oauth_manager(oauth2) # initialize oauth support second