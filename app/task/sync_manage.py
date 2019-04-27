import time
import json
import traceback
from functools import reduce


# TODO: rewrite this part with Redis queue
# Consider using rq-scheduler ???

# save job's last ran time
# key: job_id, value: timestamp
PREVIOUS_RUN_TIME = {}


def do_sync_job(worker_wrapper, account_info, job_id):
    Worker = worker_wrapper.worker_cls
    # create a worker instance
    worker = Worker(account_info['accountname'],
                          account_info['source_id'])
    try:
        worker.sync()
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
        print("Sync job failed: " + account_info['accountname'])
    # pause current job and resume next job
    resume_next_job(account_info['type'], job_id)


def resume_next_job(job_id_prefix, current_job_id=None):
    """ Pause current job(if exists) and resume next job """
    from app import scheduler
    if current_job_id != None:
        scheduler.pause_job(current_job_id)
    this_kind_of_job_ids = [
        job.id for job in scheduler.get_jobs()
        if job.id.startswith(job_id_prefix)
    ]
    next_job_id = reduce((lambda x, y:
        x if PREVIOUS_RUN_TIME.get(x, 0) < PREVIOUS_RUN_TIME.get(y, 0)
        else y), this_kind_of_job_ids)
    scheduler.resume_job(next_job_id)
    PREVIOUS_RUN_TIME[next_job_id] = time.time()


def add_sync_jobs(worker_wrapper, account_info_file, interval):
    from app import scheduler
    with open(account_info_file, "rb") as f:
        accounts = json.load(f)
        resumed = False
        for account_info in accounts:
            job_id_prefix = account_info['type']
            job_id = job_id_prefix + "_sync_" + account_info['source_id']
            job = {
                'id': job_id,
                'name': "Sync job " + account_info['accountname'],
                'func': "app.task.sync_manage:do_sync_job",
                'args': (worker_wrapper, account_info, job_id),
                'trigger': 'interval',
                'seconds': interval,
                'next_run_time': None, # pause the job initially
                'replace_existing': True,
            }
            scheduler.add_job(**job)
            print("Added sync job:", account_info['accountname'])
            if not resumed:
                resume_next_job(job_id_prefix, None)
                resumed = True




