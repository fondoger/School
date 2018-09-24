import re
from flask import request, g, jsonify, url_for
from . import api
from .utils import login_required, json_required
from .errors import forbidden, unauthorized, bad_request, not_found
from app import db, rand
from app.models import *



@api.route('/timeline', methods['GET'])
@login_required
def get_timeline():
    """
    获取个人Timeline
    参数：
    limit: 可选,default=10
    offset: 可选,default=10

    """

    # get 10 followed user's status
    followed_ids = [u.id for u in g.user.followed]
    ss = Status.query.filter(Status.user_id.in_(followed_ids))
    ss = ss.order_by(Status.timestamp.desc())
    ss = ss.offset()

