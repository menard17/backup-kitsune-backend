import json
from datetime import datetime


class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime):
            return str(z)
        else:
            return super().default(z)


def datetime_encoder(data: dict):
    return json.loads(json.dumps(data, cls=DateTimeEncoder))
