from app import rd
from app.models import *


def handle(name):
    args = name.split(":")
    if args[0] == 'new_status':
        status = Status.from_id(args[1])
        if status == None:
            return
        user_id = status.user_id
        # how to make sure user_followers are in
        followers = rd.key








