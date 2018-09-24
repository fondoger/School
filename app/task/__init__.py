__all__ = ()    # hide variables from "import *"

#from .. import scheduler
#from . import weibo
#from . import weixin
from . import sync_official_account

# app variable
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
    #weibo.add_weibo_sync_job()
    #weixin.add_weixin_sync_job()
    sync_official_account.add_sync_jobs()

