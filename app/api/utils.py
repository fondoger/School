from flask import g, request
from functools import wraps
from .errors import unauthorized, bad_request

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.is_anonymous:
            return unauthorized('@login_required, 请登陆')
        return f(*args, **kwargs)
    return decorated_function

def json_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return bad_request('@json_required, Content-Type必须是Application/json')
        return f(*args, **kwargs)
    return decorated_function
