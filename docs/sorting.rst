Sorting
=======

You can sort results with the "sort" querystring URL parameter.

Example (not urlencoded for readability)::

    GET /topics/1/posts?sort=-created,title HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json
