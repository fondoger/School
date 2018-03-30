import os
from collections import OrderedDict
from datetime import datetime
from operator import itemgetter
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


class Rank:

    def __init__(self):
        self.app = None
        self.hot_statuses_data = [] # (status_id, hot_degree)
        self.hot_statuses = []  # status_id
        self.fresh_statuses = [] # status_id
        self.mixed = []

    def init_app(self, app):
        self.app = app
        if not self.app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            scheduler = BackgroundScheduler()
            scheduler.start()
            scheduler.add_job(
                id="recalculate_rank",
                func=self._recalculate_rank,
                trigger=IntervalTrigger(days=1),
                next_run_time=datetime.now(),
                replace_existing=True,
                name="Recalculate statuses rank every day")
            atexit.register(lambda: scheduler.shutdown())

    def _recalculate_rank(self):
        from app.models import Status
        print("Recalculate rank schedule started...")
        with self.app.app_context():
            for s in Status.query:
                self.push(s)
        print("Recalculate rank schedule done!")

    def _calc_hot_degree(self, status):
        """ 热度, 每天凌晨3点重新计算
        热度影响因素
        1. 发布天数n s.timestamp       - n * 20
        2. 点赞数目n s.likes.count()   + n * 5
        3. 回复数目n s.replies.count() + n * 10
        4. 查看数目n s.views.count()   + n * 1
        """
        days = (datetime.utcnow() - status.timestamp).days * - 20
        likes = status.liked_users.count() * 5
        replies = status.replies.count() * 10
        return days + likes + replies

    def push(self, status, positive=True):
        if positive:
            try:
                index = self.fresh_statuses.index(status.id)
                self.fresh_statuses.remove(status.id)
            except:
                index = len(self.fresh_statuses)
            index = index - 30 if index - 30 >= 0 else 0
            self.fresh_statuses.insert(index, status.id)
            if len(self.fresh_statuses) > 100:
                self.fresh_statuses.pop()
        hot_degree = self._calc_hot_degree(status)
        self.hot_statuses_data = [x for x in self.hot_statuses_data if x[0] != status.id]
        self.hot_statuses_data.append((status.id, hot_degree))
        self.hot_statuses_data = sorted(self.hot_statuses_data, key=itemgetter(1), reverse=True)
        if len(self.hot_statuses_data) > 100:
            self.hot_statuses_data.pop()
        self.hot_statuses = [x[0] for x in self.hot_statuses_data]
        self.mixed = []
        h_len = len(self.hot_statuses)
        for i in range(0, int(h_len / 3)):
            self.mixed += self.hot_statuses[i*3:i*3+3]
            self.mixed.append(self.fresh_statuses[i])
        self.mixed = list(OrderedDict.fromkeys(self.mixed))

    def remove(self, status):
        self.hot_statuses_data = [x for x in self.hot_statuses_data if x[0] != status.id]
        try:
            self.hot_statuses.remove(status.id)
            self.fresh_statuses.remove(status.id)
        except:
            pass

    def get_fresh(self, offset=0, limit=1):
        return self.fresh_statuses[offset:limit]

    def get_hot(self, offset=0, limit=1):
        return self.hot_statuses[offset:limit]

    def get_mixed(self):
        return self.mixed