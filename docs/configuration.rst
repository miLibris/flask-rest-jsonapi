.. _configuration:

Configuration
=============

You have access to 3 configration keys:

* PAGE_SIZE: the default page size (default is 30)
* MAX_PAGE_SIZE: the maximum page size. If you speficy a page size greater than this value you will receive 400 Bad Request response.
* MAX_INCLUDE_DEPTH: the maximum length of an include through schema relationships
* ALLOW_DISABLE_PAGINATION: if you want to disallow to disable pagination you can set this configuration key to False
