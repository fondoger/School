from flask import current_app

def logfuncall(func):

    def wrapper(*args, **kwargs):
        if current_app.config['DEBUG']:
            print("> funcalled:", func.__name__ + "()", args, kwargs)
        return func(*args, **kwargs)

    return wrapper






