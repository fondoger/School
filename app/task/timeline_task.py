from app import rd
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


@logfuncall
def _insert_status_into_timeline(status_id, user_id):
    json = Cache.get_status_json(status_id, process_json=False)
    if json is None:
        print("#" * 10, "can't load status_json")
        return
    score = Score.from_status_json(json)
    item = Keys.timeline_status_item.format(status_id)
    for f_id in Cache.get_follower_ids(user_id):
        key = Keys.user_timeline.format(f_id)
        rd.zadd(key, {item: score})
    # insert into public timeline
    key = Keys.public_timeline
    rd.zadd(key, {item: score})


@logfuncall
def _remove_status_from_timeline(status_id, user_id):
    """item: timeline_item defined in redis_keys"""
    item = Keys.timeline_status_item.format(status_id)
    # remove from subscribers' timeline
    for f_id in Cache.get_follower_ids(user_id):
        key = Keys.user_timeline.format(f_id)
        rd.zrem(key, item)
    # remove from public timeline
    key = Keys.public_timeline
    rd.zrem(key, item)


@logfuncall
def _insert_article_into_timeline(article_id, account_id):
    json = Cache.get_article_json(article_id, process_json=False)
    if json is None:
        print("#" * 10, "can't load article_json")
        return
    score = Score.from_article_json(json)
    item = Keys.timeline_article_item.format(article_id)
    for s_id in Cache.get_subscriber_ids(account_id):
        key = Keys.user_timeline.format(s_id)
        rd.zadd(key, {item: score})
    # insert into public timeline
    key = Keys.public_timeline
    rd.zadd(key, {item: score})


@logfuncall
def _remove_article_from_timeline(article_id, account_id):
    """item: timeline_item defined in redis_keys"""
    item = Keys.timeline_article_item.format(article_id)
    # remove from subscribers' timeline
    for s_id in Cache.get_subscriber_ids(account_id):
        key = Keys.user_timeline.format(s_id)
        rd.zrem(key, item)
    # remove from public timeline
    key = Keys.public_timeline
    rd.zrem(key, item)


@logfuncall
def _handle(task_name):
    args = task_name.split(":")
    if args[0] == Keys.status_updated_prefix:
        _insert_status_into_timeline(args[1], args[2])
    elif args[0] == Keys.status_deleted_prefix:
        _remove_status_from_timeline(args[1], args[2])
    elif args[0] == Keys.article_updated_prefix:
        _insert_article_into_timeline(args[1], args[2])
    elif args[0] == Keys.article_deleted_prefix:
        _remove_article_from_timeline(args[1], args[2])


def _wrapper(arg):
    with _app.app_context():
        _handle(arg)


class LoopThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_stop = False

    def stop(self):
        self.should_stop = True
        print("Timeline task loop thread set to stop.")

    def run(self):
        print("Started timeline events task...")
        while not self.should_stop:
            result = rd.brpop(Keys.timeline_events_queue, timeout=5)
            if result is None:
                continue
            # Delay execute to avoid mysql miss
            timer = threading.Timer(1, _wrapper, [result[1].decode()])
            timer.start()
        print("Timeline task loop thread stopped")


def start():
    thread = LoopThread()
    thread.daemon = True
    thread.start()
    atexit.register(lambda: thread.stop())
