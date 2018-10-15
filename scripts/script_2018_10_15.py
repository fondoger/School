from . import *
import json
import os


def _func(filename):
    with open(filename) as f:
        accounts = json.load(f)
        for account in accounts:
            a = OfficialAccount.query.filter_by(
                accountname=account['accountname']
            ).one()
            a.page_url = account['page_url']
            db.session.add(a)
        db.session.commit()


def run():
    print("Add page_url for each accounts")
    _func('scripts/sync_buaa_news_accounts.json')
    _func('scripts/sync_weibo_accounts.json')
    _func('scripts/sync_weixin_accounts.json')

