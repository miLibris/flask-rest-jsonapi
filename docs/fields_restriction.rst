Fields restriction
==================

You can retrieve only requested fields with querystring url parameter "fields"

Example (not urlencoded for readability)::

    GET /topics/1/posts?fields[post]=title,content HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+jsona