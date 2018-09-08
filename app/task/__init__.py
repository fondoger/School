#from .. import scheduler

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
    'seconds': 3,
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
