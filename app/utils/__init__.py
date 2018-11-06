from werkzeug.http import http_date as _http_date
from datetime import datetime


def to_http_date(timestamp: float):
    if not isinstance(timestamp, float):
        raise Exception("Wrong timestamp type")
    dt = datetime.fromtimestamp(timestamp)
    return _http_date(dt.utctimetuple())
