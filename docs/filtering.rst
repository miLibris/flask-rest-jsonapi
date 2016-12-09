Filtering
=========

You can filter result with querystring url parameter "filter"

Example (not urlencoded for readability):

``GET /topics/1/posts?filter[post]=[{"field":"created","op":"gt","value":"2016-11-10"}] HTTP/1.1
  Content-Type: application/vnd.api+json
  Accept: application/vnd.api+json``
