from flask import current_app
from functools import wraps
import timeit

def logfuncall(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_app.config['DEBUG']:
            print("[LOG]Function called:", func.__name__ + "()", args, kwargs)
        return func(*args, **kwargs)
    return wrapper

def logtimeusage(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_app.config['DEBUG']:
            return func(*args, **kwargs)
        start = timeit.default_timer()
        res = func(*args, **kwargs)
        end = timeit.default_timer()
        seconds = end - start
        milliseconds = seconds * 1000
        print("[LOG]Time Usage: %.1fms" % milliseconds,
              "Func: %s()" % func.__name__)
        return res
    return wrapper







