from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_socketio import SocketIO
from app.algorithm.rank import Rank
from config import config
from app.task import add_init_jobs
import os
from . import task

db = SQLAlchemy()
# socketio = SocketIO()
scheduler = APScheduler()
login_manager = LoginManager()
login_manager.session_protection = None
login_manager.login_view = 'api.login'
rank = Rank()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # init flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    scheduler.init_app(app) # access scheduler from app.scheduler
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
		# prevents scheduler start twice (only in debug mode)
		# https://stackoverflow.com/questions/14874782
        scheduler.start()
        add_init_jobs()
    # socketio.init_app(app)

    # for calculate rank every day
    rank.init_app(app)

    # save a referece to task module
    task.init_app(app)

    # Register Blueprints
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
