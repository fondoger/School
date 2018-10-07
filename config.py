import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    DEBUG = True

    ### For sqlalchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '123'
    TRAP_BAD_REQUEST_ERRORS = False # For restful api
    TRAP_HTTP_EXCEPTIONS = False

    ### For APScheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_API_PREFIX = "/t"
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(
            url='sqlite:///' + os.path.join(basedir, 'jobstore.sqlite')
        ),
    }
    ### Others
    IMAGE_SERVER = 'http://asserts.fondoger.cn/'

    @staticmethod
    def init_app(app):
        import logging
        from logging import StreamHandler
        #file_handler = StreamHandler()
        file_handler = logging.FileHandler("app.log")
        file_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(file_handler)


class Development(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:Yq!((&1024@localhost/TEST'


config = {
    "default": Config,
    'local': Config,
    "development": Development,
}
