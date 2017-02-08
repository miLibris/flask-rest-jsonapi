# -*- coding: utf-8 -*-

from flask_rest_jsonapi.data_layers.alchemy import SqlalchemyDataLayer

__all__ = [
    'SqlalchemyDataLayer',
]

try:
    from flask_rest_jsonapi.data_layers.mongo import MongoDataLayer
except ImportError:
    pass
else:
    __all__.append('MongoDataLayer')
