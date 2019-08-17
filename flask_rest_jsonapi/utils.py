# -*- coding: utf-8 -*-

import json
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, Decimal):
            return str(obj)            
        return json.JSONEncoder.default(self, obj)
