from app import rd
from app.models import *
import threading
import app.cache as Cache
import app.cache.redis_keys as Keys
from app.utils.logger import logfuncall
import atexit

_app = None

def init_app(app):
    global _app
    _app = app

@logfuncall
def _handle(task_name):
    args = task_name.split(":")
    if args[0] == Keys.status_updated_prefix:
        status_id = args[1]
        status = Cache.get_status(status_id)
        if status == None:
            return
        user_id = status.user_id
        # how to make sure user_followers are in
        follower_ids = Cache.get_follower_ids(user_id)
        timeline_item = Keys.timeline_status_item.format(status_id)
        for follower_id in follower_ids:
            key = Keys.user_timeline.format(follower_id)
            # TODO: uncomment this
            #if rd.exists(key):
            # TODO: check where user viewed
            print(key)
            rd.zadd(key, status.score, timeline_item)
            print("Added timeline item for user:", follower_id)
    elif args[0] == Keys.status_deleted_prefix:
        status_id = args[1]
        follower_ids = Cache.get_follower_ids(user_id)
        timeline_item = Keys.timeline_status_item.format(status_id)
        for follower_id in follower_ids:
            key = Keys.user_timeline.format(follower_id)
            rd.zrem(key, timeline_item)


class LoopThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self):
        print("Started timelien events task...")
        while True:
            result = rd.brpop(Keys.timeline_events_queue)
            with _app.app_context():
                _handle(result[1])

def start():
    thread = LoopThread()
    thread.start()

























