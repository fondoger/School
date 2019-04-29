import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEBUG = True

    # For sqlalchemy
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '123'
    TRAP_BAD_REQUEST_ERRORS = False  # For restful api
    TRAP_HTTP_EXCEPTIONS = False

    # For Flask-Redis
    REDIS_URL = 'redis://localhost:6379/0'

    # For Flask-RQ2
    RQ_REDIS_URL = REDIS_URL

    # For APScheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_API_PREFIX = "/t"
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(
            url='sqlite:///' + os.path.join(basedir, 'jobstore.sqlite')
        ),
    }

    # Others
    IMAGE_SERVER = 'http://asserts.fondoger.cn/'

    @staticmethod
    def init_app(app):
        import logging
        file_handler = logging.FileHandler("app.log")
        file_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(file_handler)
        # Set logger for SQLAlchemy
        logging.basicConfig()
        # We can use follow code to log every SQL query
        # logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class Development(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://test:Yq!((&1024@localhost/TEST'

    @staticmethod
    def init_app(app):
        pass


config = {
    "default": Config,
    'local': Config,
    "development": Development,
}
