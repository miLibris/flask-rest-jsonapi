.. _routing:

Routing
=======

.. currentmodule:: flask_rest_jsonapi

The routing system is very simple and fits this pattern:

    api.route(<Resource manager>, <endpoint name>, <url_1>, <url_2>, ...)

Example:

.. code-block:: python

    # all required imports are not displayed in this example
    from flask_rest_jsonapi import Api

    api = Api()
    api.route(PersonList, 'person_list', '/persons')
    api.route(PersonDetail, 'person_detail', '/persons/<int:id>', '/computers/<int:computer_id>/owner')
    api.route(PersonRelationship, 'person_computers', '/persons/<int:id>/relationships/computers')
    api.route(ComputerList, 'computer_list', '/computers', '/persons/<int:id>/computers')
    api.route(ComputerDetail, 'computer_detail', '/computers/<int:id>')
    api.route(ComputerRelationship, 'computer_person', '/computers/<int:id>/relationships/owner')
