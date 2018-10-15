__all__ = ()    # hide variables from "import *"


# Save a app reference for weibo.py
app = None
def init_app(_app):
    global app
    app = _app

### jobs to be loaded at start
jobs = []

"""
examples:

JOBS = [
    {
        'id': 'job1',           # required
        'func': 'jobs:job1',    # required
        'args': (1, 2),
        'trigger': 'interval',
        'seconds': 10
    }
]

"""

sum = 0
def add_job():
    global sum
    sum += 1
    print(sum)

job1 = {
    'id': 'my_job_1',
    'func': 'app.task:add_job',
    'trigger': 'interval',
    'seconds': 5,
}

jobs.append(job1)

# add Weibo sync jobs

# set default values to jobs' option
for job in jobs:
    if 'coalesce' not in job:
        job['coalesce'] = True
    if 'replace_existing' not in job:
        job['replace_existing'] = True

def add_init_jobs():
    from app import scheduler
    print("add initial jobs")
    scheduler.add_job(**job1)

    # add third party account sync jobs
    from . import sync_manage
    from .weibo import Weibo
    from .weixin import Weixin
    from .buaa_news import BUAANews
    from .worker_wrapper import WorkerWrapper

    weibo = WorkerWrapper(Weibo)
    weixin = WorkerWrapper(Weixin)
    news = WorkerWrapper(BUAANews)
    sync_manage.add_sync_jobs(weibo, "scripts/sync_weibo_accounts.json", 60*10)
    sync_manage.add_sync_jobs(weixin, "scripts/sync_weixin_accounts.json", 60*10)
    sync_manage.add_sync_jobs(news, "scripts/sync_buaa_news_accounts.json", 60*10)




