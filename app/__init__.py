from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_cors import CORS
from config import config
import atexit
import os

db = SQLAlchemy()
rd = FlaskRedis()
scheduler = APScheduler()
login_manager = LoginManager()
login_manager.session_protection = None
login_manager.login_view = 'api.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    if app.debug:
        print("create app in debug mode.")
    else:
        print("create app in non-debug mode.")

    # TODO: remove this later
    CORS(app)
    # init flask extensions
    db.init_app(app)
    # Do not use decode_responses=True here,
    # because we need to store/read bytes data
    rd.init_app(app)
    login_manager.init_app(app)
    from app import task
    task.init_app(app)
    scheduler.init_app(app)  # access scheduler from app.scheduler

    scheduler.start()
    task.add_init_jobs()
    atexit.register(lambda: scheduler.shutdown())
    print("Scheduler started...")

    # start timeline task
    from app.task import timeline_task
    timeline_task.init_app(app)
    timeline_task.start()

    # Register Blueprints
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
