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

    def __init__(self, accountname, jike_id):
        self.accountname = accountname
        self.jike_id = jike_id
        self.session = Session()
        self.url = "https://app.jike.ruguoapp.com/1.0/messages/history"

    def sync(self):
        from app import db
        from app.models import Article, OfficialAccount
        from . import app

        print("Syncing WeXin %s..." % self.accountname)
        articles = self.get_articles()
        with app.app_context():
            account = OfficialAccount.query.filter_by(
                accountname=self.accountname).one()
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
                        extra_desc=article['linkInfo']['title'][:64],
                        official_account=account)
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



