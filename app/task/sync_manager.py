import time
import json
import traceback
import importlib
from datetime import datetime
from app.models import OfficialAccount
from typing import Tuple
from functools import reduce
from app import db
from app.models import Article, OfficialAccount
from . import app

# TODO: rewrite this part with Redis queue
# Consider using rq-scheduler ???

# save job's last ran time
# key: job_id, value: timestamp

PREVIOUS_RUN_TIME = {}


def pick_next_account(website_type: str) -> Tuple[str, str]:
    """从数据库中挑选下一个将被更新的公众号

    :param website_type:
    :return: (accountname, account_key)
    """
    with app.app_context():
        account = OfficialAccount.query\
            .filter_by(external_sync=True, external_type=website_type)\
            .order_by(OfficialAccount.external_synced_at).first()
        if account is None:
            raise Exception("can't find an account to sync, website_type:%s" % website_type)
        account.external_synced_at = datetime.utcnow()
        db.session.add(account)
        db.session.commit()
        return account.accountname, account.external_key


def do_sync_job(website_type: str, worker_module_name: str, worker_class_name: str):
    try:
        accountname, account_key = pick_next_account(website_type)
        worker_cls = getattr(importlib.import_module(worker_module_name), worker_class_name)
        worker = worker_cls(accountname, account_key)
        worker.sync()
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        print("Sync job failed: ")


def add_sync_job(website_type, module_name, class_name, interval):
    from app import scheduler
    job = {
        'id': 'sync_' + website_type,
        'name': "Sync job ",
        'func': "app.task.sync_manager:do_sync_job",
        'args': (website_type, module_name, class_name),
        'trigger': 'interval',
        'seconds': interval,
        'next_run_time': datetime.now(),
        'replace_existing': True,
    }
    scheduler.add_job(**job)
    print("Added sync job:", website_type)
