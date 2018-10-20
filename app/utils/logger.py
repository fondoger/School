

def logfuncall(func):

    def wrapper(*args, **kwargs):
        print("> funcalled:", func.__name__ + "()", args, kwargs)
        return func(*args, **kwargs)

    return wrapper






