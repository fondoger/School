from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.algorithm.rank import Rank
from config import config


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = None
login_manager.login_view = 'api.login'
rank = Rank()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)

    # for calculate rank every day
    rank.init_app(app)

    # Register Blueprints
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app