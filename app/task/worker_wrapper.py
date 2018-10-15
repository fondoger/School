

"""
This class is used to make worker class `serializable` for flask-apscheduler
"""


class WorkerWrapper(dict):

    def __init__(self, worker_cls):
        super().__init__(worker_cls_name=worker_cls.__name__)
        self.worker_cls = worker_cls
