import time
import os
import json
import logging
from requests import Session
from datetime import datetime
from functools import reduce
from sqlalchemy.sql import exists
from sqlalchemy import and_

# save job previous run time
# key:job_id, value:timestamp
previous_run_time = {}


class Weibo:
    """
    :var str account_id: id of OfficialAccount
    :var str weibo_id: id of Weibo
    """

    def __init__(self, account_id, weibo_id):
        self.account_id = account_id
        self.weibo_id = weibo_id
        self.session = Session()
        self.url = 'https://m.weibo.cn/profile/info?uid=' + weibo_id

    def sync(self):
        from app import db
        from app.models import Article
        from . import app

        print("Syncing Weibo:", self.account_id)
        statuses = self.get_statuses()
        with app.app_context():
            new_statuses = [
                status for status in statuses
                if not db.session.query(exists().where(and_(
                    Article.type_id==Article.TYPES['WEIBO'],
                    Article.extra_key==status['id'],
                ))).scalar()
            ]
            print("Found %d new in %d weibo statuses" %
                    (len(new_statuses), len(statuses)))
            if len(new_statuses) == 0:
                return
            for status in new_statuses:
                data = json.dumps(status, ensure_ascii=False)
                article = Article(type="WEIBO",
                        timestamp=self.get_timestamp(status),
                        extra_key=status['id'],
                        extra_data=data,
                        extra_desc=status['text'],
                        extra_url='https://m.weibo.cn/detail/' + status['id'],
                        official_account_id=self.account_id)
                db.session.add(article)
            db.session.commit()

    def get_statuses(self):
        res = self.session.get(self.url, timeout=5)
        return res.json()['data']['statuses']

    def get_timestamp(self, json):
        return datetime.strptime(json['created_at'],
            "%a %b %d %H:%M:%S %z %Y")


def weibo_sync_job(account_id, weibo_id, job_id):
    # do your stuff
    weibo = Weibo(account_id, weibo_id)
    try:
        weibo.sync()
    except Exception as e:
        print(e)
        print("Sync weibo %s failed!" % weibo_id)
    # pause current job and resume next job
    resume_next_job(job_id)

def resume_next_job(current_job_id=None):
    """ Pause current job(if exists) and resume next job"""
    from app import scheduler
    if current_job_id is not None:
        scheduler.pause_job(current_job_id)
    weibo_job_ids = [
        job.id for job in scheduler.get_jobs()
        if job.id.startswith("sync_weibo_")
    ]
    next_job_id = reduce((lambda x, y: x if previous_run_time.get(x, 0) < previous_run_time.get(y, 0) else y), weibo_job_ids)
    scheduler.resume_job(next_job_id)
    previous_run_time[next_job_id] = time.time()


def add_weibo_sync_job():
    from app import scheduler
    path = os.path.join(os.path.dirname(__file__), 'sync_weibo.json')
    with open(path) as f:
        accounts = json.load(f)
        for account in accounts:
            job_id = 'sync_weibo_' + account['account_id']
            job = {
                'id': job_id,
                'name': 'Sync ' + account['description'],
                'func': 'app.task.weibo:weibo_sync_job',
                'args': (account['account_id'], account['weibo_id'], job_id),
                'trigger': 'interval',
                'seconds': 10,
                'next_run_time': None,  # pause job
                'replace_existing': True,
            }
            scheduler.add_job(**job)
    resume_next_job(None)

