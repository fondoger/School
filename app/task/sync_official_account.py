import time
import os
import json
from requests import Session
from datetime import datetime
from functools import reduce
from sqlalchemy.sql import exists
from sqlalchemy import and_
from .weibo import Weibo
from .weixin import Weixin


# save job's last runned time
# key: job_id, value: timestamp
PREVIOUS_RUN_TIME = {}


def sync_job(account, job_id):
    Syncler = Weibo if account['type'] == 'WEIBO' else Weixin
    syncler = Syncler(account['accountname'], account['source_id'])
    try:
        syncler.sync()
    except Exception as e:
        print(str(e))
        print("Sync job failed: " + account['accountname'])
    # pause current job and resume next job
    resume_next_job(account['type'], job_id)


def resume_next_job(job_type, current_job_id=None):
    """ Pause current job(if exists) and resume next job """
    from app import scheduler
    if current_job_id != None:
        scheduler.pause_job(current_job_id)
    sync_job_ids = [
        job.id for job in scheduler.get_jobs()
        if job.id.startswith(job_type + "_sync")
    ]
    next_job_id = reduce((lambda x, y:
        x if PREVIOUS_RUN_TIME.get(x, 0) < PREVIOUS_RUN_TIME.get(y, 0)
        else y), sync_job_ids)
    scheduler.resume_job(next_job_id)
    PREVIOUS_RUN_TIME[next_job_id] = time.time()


def add_sync_jobs():
    from app import scheduler
    with open("scripts/sync_official_accounts.json") as f:
        accounts = json.load(f)
        for account in accounts:
            job_id = account['type'] + "_sync_" + account['source_id']
            interval =  8 if account['type'] == 'WEIBO' else 10
            job = {
                'id': job_id,
                'name': 'Sync job ' + account['accountname'],
                'func': 'app.task.sync_official_account:sync_job',
                'args': (account, job_id),
                'trigger': 'interval',
                'seconds': interval,
                'next_run_time': None,  # pause job at start
                'replace_existing': True,
            }
            scheduler.add_job(**job)
            print("add sync job: " + account['accountname'])
        resume_next_job("WEIBO", None)
        resume_next_job("WEIXIN", None)
