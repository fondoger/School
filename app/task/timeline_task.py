from app import rd
from app.models import *
import threading
import app.cache as Cache
import app.cache.redis_keys as Keys
from app.utils.logger import logfuncall

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
        timeline_item = Keys.timeline_status.format(status_id)
        for follower_id in follower_ids:
            key = Keys.user_timeline.format(follower_id)
            # TODO: uncomment this
            #if rd.exists(key):
            # TODO: check where user viewed
            rd.zadd(key, status.score, timeline_item)
    elif args[0] == Keys.status_deleted_prefix:
        status_id = args[1]
        follower_ids = Cache.get_follower_ids(user_id)
        timeline_item = Keys.timeline_status.format(status_id)
        for follower_id in follower_ids:
            key = Keys.user_timeline.format(follower_id)
            rd.zrem(key, timeline_item)

def _loop():
    print("Started timeline events task...")
    while True:
        task_name = rd.brpop(Keys.timeline_events_queue)[1].decode()
        with _app.app_context():
            _handle(task_name)

def start():
    thread = threading.Thread(target=_loop)
    thread.start()
























