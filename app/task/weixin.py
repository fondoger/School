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

class Weixin:
    """
    :var str account_id: id of OfficialAccount
    :var str jike_id: id of jike topic
    """

    def __init__(self, account_id, jike_id):
        self.account_id = account_id
        self.jike_id = jike_id
        self.session = Session()
        self.url = "https://app.jike.ruguoapp.com/1.0/messages/history"

    def sync(self):
        from app import db
        from app.models import Article
        from . import app

        print("Syncing WeXin Official Account")
        articles = self.get_articles()
        with app.app_context():
            new_articles = [
                article for article in articles
                if not db.session.query(exists().where(and_(
                    Article.type_id==Article.TYPES['WEIXIN'],
                    Article.extra_key==article['id']
                ))).scalar()
            ]
            print("Found %d new in %d weixin articles" %
                  (len(new_articles), len(articles)))
            if len(new_articles) == 0:
                return
            for article in new_articles:
                data = json.dumps(article, ensure_ascii=False)
                article = Article(type="WEIXIN",
                        timestamp=self.get_timestamp(article),
                        extra_key=article['id'],
                        extra_url=article['linkInfo']['originalLinkUrl'],
                        extra_data=data,
                        extra_desc=article['linkInfo']['title'],
                        official_account_id=self.account_id)
                db.session.add(article)
            db.session.commit()


    def get_articles(self):
        headers = {
            'App-Version': '4.12.0',
            'Referer': 'https://m.okjike.com/topics/' + self.jike_id,
        }
        data = { "loadMoreKey": None, "topic": self.jike_id, "limit": 10 }
        res = self.session.post(self.url, data=data, timeout=5, headers=headers)
        return res.json()['data']


    def get_timestamp(self, json):
        return datetime.strptime(json['createdAt'][:-5] + "+0000",
                "%Y-%m-%dT%H:%M:%S%z")



def weixin_sync_job(account_id, jike_id, job_id):
    weixin = Weixin(account_id, jike_id)
    try:
        weixin.sync()
    except Exception as e:
        print(str(e))
        print("Sync weixin %s failed" % jike_id)
    # pause current job and resume next job
    resume_next_job(job_id)


def resume_next_job(current_job_id=None):
    """ Pause current job(if exists) and resume next job"""
    from app import scheduler
    if current_job_id is not None:
        scheduler.pause_job(current_job_id)
    weixin_job_ids = [
        job.id for job in scheduler.get_jobs()
        if job.id.startswith("sync_weixin_")
    ]
    next_job_id = reduce((lambda x, y: x
        if previous_run_time.get(x, 0) < previous_run_time.get(y, 0)
        else y), weixin_job_ids)
    scheduler.resume_job(next_job_id)
    previous_run_time[next_job_id] = time.time()


def add_weixin_sync_job():
    from app import scheduler
    path = os.path.join(os.path.dirname(__file__), 'sync_weixin.json')
    with open(path) as f:
        accounts = json.load(f)
        for account in accounts:
            job_id = 'sync_weixin_' + account['account_id']
            job = {
                'id': job_id,
                'name': 'Sync ' + account['description'],
                'func': 'app.task.weixin:weixin_sync_job',
                'args': (account['account_id'], account['jike_id'], job_id),
                'trigger': 'interval',
                'seconds': 10,
                'next_run_time': None, # pause at start
                'replace_existing': True,
            }
            scheduler.add_job(**job)
    resume_next_job(None)



