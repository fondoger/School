from app import db, models
from app.models import *
from sqlalchemy.sql import exists
import json
import os


def generate_buaa_news_accounts():
    print('generating official accounts...')
    path = os.path.join(os.path.dirname(__file__), 'sync_buaa_news_accounts.json')
    with open(path) as f:
        accounts = json.load(f)
        for account in accounts:
            if db.session.query(exists().where(
                    OfficialAccount.accountname==account['accountname']
                    )).scalar():
                print("official account %s already exits" % account['accountname'])
                continue
            a = OfficialAccount(accountname=account['accountname'],
                    avatar=account['avatar'], description=account['description'])
            db.session.add(a)
            print("create official account %s" % account['accountname'])
        db.session.commit()
        print("generate offical account success")
