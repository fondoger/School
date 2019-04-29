

# Save a app reference for weibo.py
app = None


def init_app(_app):
    global app
    app = _app


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


def add_init_jobs():

    # add third party account sync jobs
    from . import sync_manager

    sync_manager.add_sync_job('WEIBO', 'app.task.weibo', 'Weibo', 60 * 5)
    sync_manager.add_sync_job('WEIXIN', 'app.task.weixin', 'Weixin', 60 * 2)
    sync_manager.add_sync_job('BUAANEWS', 'app.task.buaa_news', 'BUAANews', 60 * 5)
    sync_manager.add_sync_job('BUAAART', 'app.task.buaa_art_gallery', 'BUAAArt', 60 * 60)
