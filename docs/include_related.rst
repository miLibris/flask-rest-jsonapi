.. _include_related:

Include related document(s)
===========================

.. currentmodule:: flask_rest_jsonapi

You can include related object(s) details to response with the querystring parameter called include. You can use "include" parameter on any kind of url (classical CRUD url or relationships url) and any kind of http methods as long as method return data.

Example:

.. sourcecode:: http

    GET /persons/1?include=computers HTTP/1.1
    Accept: application/vnd.api+json

You can even use relationships with include

Example:

.. sourcecode:: http

    GET /persons/1?include=computers.person HTTP/1.1
    Accept: application/vnd.api+json

I know it is an absurd example because it will include details of related person computers and details of the person that is already in reponse. But it is just for example.
