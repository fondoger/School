from app import db, models
from app.models import *
from sqlalchemy.sql import exists
import json
import os


def _func(path):
    print(path)
    with open(path) as f:
        accounts = json.load(f)
        for account in accounts:
            if db.session.query(exists().where(
                    OfficialAccount.accountname==account['accountname']
                    )).scalar():
                print("official account %s already exits" % account['accountname'])
                continue
            a = OfficialAccount(accountname=account['accountname'],
                    avatar=account['avatar'], description=account['description'],
                    page_url=account['page_url'])
            db.session.add(a)
            print("create official account %s" % account['accountname'])
        db.session.commit()
        print("generate offical account success")

def generate_official_accounts():
    print('generating official accounts...')
    paths = [
        'scripts/sync_buaa_art_news_accounts.json',
        'scripts/sync_buaa_news_accounts.json',
        'scripts/sync_weibo_accounts.json',
        'scripts/sync_weixin_accounts.json',
    ]
    for p in paths:
        _func(p)

