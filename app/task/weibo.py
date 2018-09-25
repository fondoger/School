import time
import pytz
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

    def __init__(self, accountname, weibo_id):
        self.accountname = accountname
        self.weibo_id = weibo_id
        self.session = Session()
        self.url = 'https://m.weibo.cn/profile/info?uid=' + weibo_id

    def sync(self):
        from app import db
        from app.models import Article, OfficialAccount
        from . import app

        print("Syncing Weibo %s..." % self.accountname)
        statuses = self.get_statuses()
        with app.app_context():
            print(self.accountname)
            account = OfficialAccount.query.filter_by(
                accountname=self.accountname).one()
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
                        extra_desc=status['text'][:64],
                        extra_url='https://m.weibo.cn/detail/' + status['id'],
                        official_account=account)
                db.session.add(article)
            db.session.commit()

    def get_statuses(self):
        res = self.session.get(self.url, timeout=5)
        return res.json()['data']['statuses']

    def get_timestamp(self, json):
        return datetime.strptime(json['created_at'],
            "%a %b %d %H:%M:%S %z %Y").astimezone(pytz.utc)

