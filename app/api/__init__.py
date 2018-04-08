from flask import Blueprint

api = Blueprint('api', __name__)

from . import users, statuses, other, groups, sales, socketio, messages