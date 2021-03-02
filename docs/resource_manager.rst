.. _resource_manager:

Resource Manager
================

.. currentmodule:: flask_rest_jsonapi

Resource manager is the link between your logical data abstraction, your data layer and optionally other software. It is the place where logic management of your resource is located.

Flask-REST-JSONAPI provides three kinds of resource managers with default methods implemented according to the JSON:API 1.0 specification:

* **ResourceList**: provides get and post methods to retrieve or create a collection of objects.
* **ResourceDetail**: provides get, patch and delete methods to retrieve details of an object, update or delete it
* **ResourceRelationship**: provides get, post, patch and delete methods to get, create, update and delete relationships between objects.

You can rewrite each default method implementation to customize it. If you rewrite all default methods of a resource manager or if you rewrite a method and disable access to others, you don't have to set any attributes of your resource manager.

Required attributes
-------------------

If you want to use one of the resource manager default method implementations you have to set two required attributes in your resource manager: schema and data_layer.

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

All resource managers are inherited from flask.views.MethodView so you can provide optional attributes to your resource manager:

    :methods: a list of methods this resource manager can handle. If you don't specify any method, all methods are handled.
    :decorators: a tuple of decorators plugged into all methods that the resource manager can handle

You can provide default schema kwargs for each resource manager method with these optional attributes:

* **get_schema_kwargs**: a dict of default schema kwargs in get method
* **post_schema_kwargs**: a dict of default schema kwargs in post method
* **patch_schema_kwargs**: a dict of default schema kwargs in patch method
* **delete_schema_kwargs**: a dict of default schema kwargs in delete method

Each method of a resource manager gets a pre- and postprocess method that takes view args and kwargs as parameters for the pre process methods, and the result of the method as parameter for the post process method. Thanks to this you can process custom code before and after the method processes. Available methods to override are:

    :before_get: preprocess method of the get method
    :after_get: postprocess method of the get method
    :before_post: preprocess method of the post method
    :after_post: postprocess method of the post method
    :before_patch: preprocess method of the patch method
    :after_patch: postprocess method of the patch method
    :before_delete: preprocess method of the delete method
    :after_delete: postprocess method of the delete method

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
           """Perform custom operations here. View args and kwargs are provided as parameter
           """

        def after_patch(result):
           """Perform custom operations here. Add something to the result of the view.
           """

ResourceList
------------

ResourceList manager has its own optional attributes:

    :view_kwargs: if you set this flag to True, view kwargs will be used to compute the list URL. If you have a list URL pattern with parameters such as ``/persons/<int:id>/computers`` you have to set this flag to True

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

This minimal ResourceDetail configuration provides a GET, PATCH and DELETE interface to retrieve details of an object, update and delete it with all-powerful features like sparse fieldsets and including related objects.

If your schema has relationship fields you can update an object and also update its links to (one or more) related objects at the same time. For an example see :ref:`quickstart`.

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

This minimal ResourceRelationship configuration provides a GET, POST, PATCH and DELETE interface to retrieve, create, update or delete one or more relationships between objects with all-powerful features like sparse fieldsets and including related objects.
