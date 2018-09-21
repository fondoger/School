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

class WeXin:
    """
    :var str account_id: id of OfficialAccount
    :var str jike_id: id of jike topic
    """

    def __init__(self, account_id, jike_id):
        self.account_id = account_id
        self.weibo_id = weibo_id
        self.session = Session()

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
                data = json.dumps(status, ensure_ascii=False)
                article = Article(type="WEIXIN",
                        timestamp=self.get_timestamp(article),
                        extra_key=article['id'],
                        extra_data=data,
                        official_account_id=self.account_id)
                db.session.add(article)
            db.session.commit()


    def get_timestamp(self, json):
        kk
