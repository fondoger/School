from sqlalchemy import event
from . import *

@event.listen_for(User.followers, "init_collection")
def my_listener(*args):
    print(args)

