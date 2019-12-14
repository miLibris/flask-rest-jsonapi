# Changelog
## 0.30.10
* Fix for nested fields under Marshmallow 3, thanks to @pacoyang (https://github.com/TMiguelT/flapison/pull/11)

## 0.30.9
* Allow simple filters to have list values, e.g. `filter[id]=1,2,3`

## 0.30.8
* Allow relationships to be compared to scalars (https://github.com/TMiguelT/flapison/pull/8)

## 0.30.7
* Be more relaxed about the Content-Type header. We ignore its value unless it's a POST or PATCH request, since we don't actually use the request body for GET and DELETE

## 0.30.6
* Be more relaxed about the Accept header. In general, allow no Accept header, or `*/*`. Assume these are `application/vnd.api+json`

## 0.30.5
* Fix issues involving Content-Type headers with arguments, e.g. 'text/html; charset=UTF-8'
* Stop supporting Python 3.5 (unfortunately), due to [marshmallow-jsonapi](https://github.com/marshmallow-code/marshmallow-jsonapi) dropping support

## 0.30.4
* Allow providing content parsers and renderers as class variables (https://github.com/TMiguelT/flapison/pull/4)

## 0.30.3
* Allow providing the `*_schema_kwargs` family as a function (https://github.com/miLibris/flask-rest-jsonapi/pull/179)

## 0.30.2 (first release post-fork)
* Allow custom content types (https://github.com/miLibris/flask-rest-jsonapi/pull/171)
* Bump Marshmallow to Python 3, and remove Python 2 support (https://github.com/miLibris/flask-rest-jsonapi/pull/172)
* Automatically filter resource lists by their parents (https://github.com/miLibris/flask-rest-jsonapi/pull/177)
* Assign the correct endpoint string to each Resource instance (https://github.com/miLibris/flask-rest-jsonapi/pull/178)