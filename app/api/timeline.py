import re
from flask import request, g, jsonify, url_for
from . import api
from .utils import login_required, json_required
from .errors import forbidden, unauthorized, bad_request, not_found
from app import db, rd
from app.models import *
import app.cache as Cache
import app.cache.redis_keys as Keys


@api.route('/timeline', methods=['GET'])
@login_required
def get_timeline():
    """
    获取个人Timeline
    参数：
    limit: 可选,default=10
    offset: 可选,default=10
    """
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 10, type=int)
    key = Keys.user_timeline.format(g.user.id)
    print("View:", key)
    if rd.exists(key):
        """element: type:id,  type=s|a"""
        datas = rd.zrevrange(key, offset, offset+limit)
        items = [ d.decode() for d in datas ]
        status_ids = []
        article_ids = []
        for item in items:
            if item[0] == Keys.timeline_status_prefix:
                status_ids.append(item[2:])
            elif item[0] == Keys.timeline_status_prefix:
                article_ids.append(item[2:])
            else:
                raise Exception("No such type")
        statuses = Cache.get_statuses(status_ids)
        articles = []
        res_map = {}
        for s in statuses:
            res_map[Keys.timeline_status_item.format(s.id)]  = s
        for a in articles:
            res_map[Keys.timeline_stauts_item.format(a.id)] = a
        res = [ res_map[t].to_json() for t in items if t in res_map ]
        return jsonify(res)
    return bad_request("User has no timeline currently")













