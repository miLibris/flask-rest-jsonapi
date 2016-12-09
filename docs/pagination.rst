Pagination
==========

You can control the pagination with querystring url parameter "page"

Example (not urlencoded for readability)::

    GET /topics/1/posts?page[size]=2&page[number]=3 HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json

If you want to disable pagination juste set page size to 0

Example (not urlencoded for readability)::

    GET /topics/1/posts?page[size]=0 HTTP/1.1
    Content-Type: application/vnd.api+json
    Accept: application/vnd.api+json
