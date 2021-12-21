import json
from datetime import date, datetime


class DateTimeEncoder(json.JSONEncoder):
    def default(self, z):
        if isinstance(z, datetime):
            print("date")
            print(z)
            return str(z)
        if isinstance(z, date):
            print("date2")
            print(z)
            return z.strftime("%Y-%m-%d")
        if isinstance(z, bytes):
            return z.decode("utf-8")
        else:
            return super().default(z)


def datetime_encoder(data: dict):
    result = json.loads(json.dumps(data, cls=DateTimeEncoder))
    return result
