Filtering
=========

You can filter results with the querystring url parameter "filter"

Example (not urlencoded for readability)::

    GET /topics/1/posts?filter[post]=[{"field":"created","op":"gt","value":"2016-11-10"}] HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json

You can add multiple filters but "or" expressions are not implemented yet. I will create a filtering system like Flask-Restless as soon
as possible.

Multiple filter example::

    GET /topics/1/posts?filter[post]=[{"field":"created","op":"gt","value":"2016-11-10"},{"field":"title","op":"like","value":"%test%"}] HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json

Available operations depend on the data layer chosen. Read the "Available operations" section of your data layer documentation
to learn more.
