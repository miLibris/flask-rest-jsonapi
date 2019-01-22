.. _resource_manager:

Resource Manager
================

.. currentmodule:: flask_rest_jsonapi

Resource manager is the link between your logical data abstraction, your data layer and optionally other software. It is the place where logic management of your resource is located.

Flask-REST-JSONAPI provides 3 kinds of resource manager with default methods implementation according to the JSONAPI 1.0 specification:

* **ResourceList**: provides get and post methods to retrieve a collection of objects or create one.
* **ResourceDetail**: provides get, patch and delete methods to retrieve details of an object, update an object and delete an object
* **ResourceRelationship**: provides get, post, patch and delete methods to get relationships, create relationships, update relationships and delete relationships between objects.

You can rewrite each default methods implementation to make custom work. If you rewrite all default methods implementation of a resource manager or if you rewrite a method and disable access to others, you don't have to set any attribute of your resource manager.

Required attributes
-------------------

If you want to use one of the resource manager default method implementation you have to set 2 required attributes in your resource manager: schema and data_layer.

    :schema: the logical data abstraction used by the resource manager. It must be a class inherited from marshmallow_jsonapi.schema.Schema.
    :data_layer: data layer information used to initialize your data layer (If you want to learn more: :ref:`data_layer`)

Example:

.. code-block:: python

    from flask_rest_jsonapi import ResourceList
    from your_project.schemas import PersonSchema
    from your_project.models import Person
    from your_project.extensions import db

    class PersonList(ResourceList):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}

Optional attributes
-------------------

All resource managers are inherited from flask.views.MethodView so you can provides optional attributes to your resource manager:

    :methods: a list of methods this resource manager can handle. If you don't specify any method, all methods are handled.
    :decorators: a tuple of decorators plugged to all methods that the resource manager can handle

You can provide default schema kwargs for each resource manager methods with these optional attributes:

* **get_schema_kwargs**: a dict of default schema kwargs in get method
* **post_schema_kwargs**: a dict of default schema kwargs in post method
* **patch_schema_kwargs**: a dict of default schema kwargs in patch method
* **delete_schema_kwargs**: a dict of default schema kwargs in delete method

Each method of a resource manager gets a pre and post process methods that takes view args and kwargs as parameters for the pre process methods, and the result of the method as parameter for the post process method. Thanks to this you can make custom work before and after the method process. Available methods to override are:

    :before_get: pre process method of the get method
    :after_get: post process method of the get method
    :before_post: pre process method of the post method
    :after_post: post process method of the post method
    :before_patch: pre process method of the patch method
    :after_patch: post process method of the patch method
    :before_delete: pre process method of the delete method
    :after_delete: post process method of the delete method

Example:

.. code-block:: python

    from flask_rest_jsonapi import ResourceDetail
    from your_project.schemas import PersonSchema
    from your_project.models import Person
    from your_project.security import login_required
    from your_project.extensions import db

    class PersonList(ResourceDetail):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}
        methods = ['GET', 'PATCH']
        decorators = (login_required, )
        get_schema_kwargs = {'only': ('name', )}

        def before_patch(*args, **kwargs):
           """Make custom work here. View args and kwargs are provided as parameter
           """

        def after_patch(result):
           """Make custom work here. Add something to the result of the view.
           """

ResourceList
------------

ResourceList manager has its own optional attributes:

    :view_kwargs: if you set this flag to True view kwargs will be used to compute the list url. If you have a list url pattern with parameter like that: /persons/<int:id>/computers you have to set this flag to True

Example:

.. code-block:: python

    from flask_rest_jsonapi import ResourceList
    from your_project.schemas import PersonSchema
    from your_project.models import Person
    from your_project.extensions import db

    class PersonList(ResourceList):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}

This minimal ResourceList configuration provides GET and POST interface to retrieve a collection of objects and create an object with all powerful features like pagination, sorting, sparse fieldsets, filtering and including related objects.

If your schema has relationship field(s) you can create an object and link related object(s) to it in the same time. For an example see :ref:`quickstart`.

ResourceDetail
--------------

Example:

.. code-block:: python

    from flask_rest_jsonapi import ResourceDetail
    from your_project.schemas import PersonSchema
    from your_project.models import Person
    from your_project.extensions import db

    class PersonDetail(ResourceDetail):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}

This minimal ResourceDetail configuration provides GET, PATCH and DELETE interface to retrieve details of objects, update an objects and delete an object with all powerful features like sparse fieldsets and including related objects.

If your schema has relationship field(s) you can update an object and also update his link(s) to related object(s) in the same time. For an example see :ref:`quickstart`.

ResourceRelationship
--------------------

Example:

.. code-block:: python

    from flask_rest_jsonapi import ResourceRelationship
    from your_project.schemas import PersonSchema
    from your_project.models import Person
    from your_project.extensions import db

    class PersonRelationship(ResourceRelationship):
        schema = PersonSchema
        data_layer = {'session': db.session,
                      'model': Person}

This minimal ResourceRelationship configuration provides GET, POST, PATCH and DELETE interface to retrieve relationship(s), create relationship(s), update relationship(s) and delete relationship(s) between objects with all powerful features like sparse fieldsets and including related objects.
