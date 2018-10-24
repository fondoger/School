from app import rd
from app.models import *
import threading
import app.cache as Cache
import app.cache.redis_keys as Keys
import app.utils.score as Score
from app.utils.logger import logfuncall
import atexit

_app = None

def init_app(app):
    global _app
    _app = app

def _insert_item_into_followers_timeline(user_id, score, item):
    """item: timeline_item defined in redis_keys"""
    follower_ids = Cache.get_follower_ids(user_id)
    for follower_id in follower_ids:
        key = Keys.user_timeline.format(follower_id)
        rd.zadd(key, score, item)
        # Do not update expire for user_timeline here

def _insert_item_into_public_timeline(score, item):
    """item: timeline_item defined in redis_keys"""
    key = Keys.public_timeline
    rd.zadd(key, score, item)

def _remove_item_from_followers_timeline(user_id, item):
    """item: timeline_item defined in redis_keys"""
    follower_ids = Cache.get_follower_ids(user_id)
    for follower_id in follower_ids:
        key = Keys.user_timeline.format(follower_id)
        rd.zrem(key, item)

def _remove_item_from_public_timeline(item):
    """item: timeline_item defined in redis_keys"""
    key = Keys.public_timeline
    rd.zrem(key, item)

@logfuncall
def _handle(task_name):
    args = task_name.split(":")
    if args[0] == Keys.status_updated_prefix:
        status_id = args[1]
        status = Cache.get_status(status_id)
        if status == None:
            return
        owner_id = status.user.id
        score = status.score
        item = Keys.timeline_status_item.format(status_id)
        _insert_item_into_public_timeline(score, item)
        _insert_item_into_followers_timeline(owner_id, score, item)
    elif args[0] == Keys.status_deleted_prefix:
        status_id = args[1]
        owner_id = args[2]
        item = Keys.timeline_status_item.format(status_id)
        _remove_item_from_public_timeline(item)
        _remove_item_from_followers_timeline(owner_id, item)


class LoopThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_stop = False
    def stop(self):
        self.should_stop = True
        print("Timeline task loop thread set to stop.")
    def run(self):
        print("Started timelien events task...")
        while not self.should_stop:
            result = rd.brpop(Keys.timeline_events_queue,
                     timeout=5)
            if result == None:
                continue
            with _app.app_context():
                _handle(result[1].decode())
        print("Timeline task loop thread stopped")

def start():
    thread = LoopThread()
    thread.daemon = True
    thread.start()
    atexit.register(lambda: thread.stop())

























