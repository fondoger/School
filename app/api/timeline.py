from flask import request, g, jsonify
from . import api
from .utils import login_required
from app import db, rd
from app.utils.logger import logtimeusage, logfuncall
import app.utils.score as Score
from sqlalchemy.sql import text
import app.cache as Cache
import app.cache.redis_keys as KEYS


@logfuncall
def _load_user_timeline(id):
    """Load user timeline from database"""
    sql = """
    select * from (
        select 0 as kind, id, timestamp
        from statuses where user_id=:UID or user_id in (
            select followed_id from user_follows as F
            where F.follower_id=:UID
        )
        union
        select 1 as kind, id, timestamp
        from articles where official_account_id in (
            select official_account_id from subscriptions as S
            where S.users_id=:UID
        )
    ) as t order by timestamp DESC limit :LIMIT offset :OFFSET;
    """  # NOTE: `S.users_id` is a typo of column name(Don't change)
    key = KEYS.user_timeline.format(id)
    result = db.engine.execute(text(sql), UID=id, LIMIT=100, OFFSET=0)
    result = list(result)
    pairs = {}
    for item in result:
        if item['kind'] == 0:       # status
            timeline_item = KEYS.timeline_status_item.format(item['id'])
            score = Score.timestamp_to_score(item['timestamp'])
            pairs[timeline_item] = score
        elif item['kind'] == 1:     # article
            timeline_item = KEYS.timeline_article_item.format(item['id'])
            score = Score.timestamp_to_score(item['timestamp'])
            pairs[timeline_item] = score
    if pairs:
        rd.zadd(key, pairs)
        rd.expire(key, KEYS.user_timeline_expire)


@api.route('/timeline', methods=['GET'])
@logtimeusage
@login_required
def get_timeline():
    """
    获取个人Timeline
    参数：
    limit: 可选,default=10
    offset: 可选,default=10
    """
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    key = KEYS.user_timeline.format(g.user.id)
    print("View:", key)
    if not rd.exists(key):
        # A long time no-logged in user comes back
        # rd.rpush(Keys.timeline_events_queue,
        #         Keys.user_returned.format(g.user.id))
        _load_user_timeline(g.user.id)
    """element: type:id,  type=s|a"""
    datas = rd.zrevrange(key, offset, offset + limit - 1)
    rd.expire(key, KEYS.user_timeline_expire)
    items = [d.decode() for d in datas]
    print("Timeline items:", items)
    status_ids = []
    article_ids = []
    for item in items:
        if item[0] == KEYS.timeline_status_prefix:
            status_ids.append(item[2:])
        elif item[0] == KEYS.timeline_article_prefix:
            article_ids.append(item[2:])
        else:
            raise Exception("No such type")
    statuses = Cache.multiget_status_json(status_ids)
    articles = Cache.multiget_article_json(article_ids)
    res_map = {}
    for s in statuses:
        item_key = KEYS.timeline_status_item.format(s['id'])
        res_map[item_key] = s
    for a in articles:
        item_key = KEYS.timeline_article_item.format(a['id'])
        res_map[item_key] = a
    res = [res_map[t] for t in items if t in res_map]
    return jsonify(res)


@api.route('/public_timeline', methods=['GET'])
@login_required
def get_public_timeline():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    datas = rd.zrevrange(KEYS.public_timeline, offset, offset + limit - 1)
    print(offset, limit, datas)
    items = [d.decode() for d in datas]
    status_ids = []
    article_ids = []
    for item in items:
        if item[0] == KEYS.timeline_status_prefix:
            status_ids.append(item[2:])
        elif item[0] == KEYS.timeline_article_prefix:
            article_ids.append(item[2:])
        else:
            raise Exception("No such type")
    statuses = Cache.multiget_status_json(status_ids)
    articles = Cache.multiget_article_json(article_ids)
    res_map = {}
    for s in statuses:
        item_key = KEYS.timeline_status_item.format(s['id'])
        res_map[item_key] = s
    for a in articles:
        item_key = KEYS.timeline_article_item.format(a['id'])
        res_map[item_key] = a
    res = [res_map[t] for t in items if t in res_map]
    return jsonify(res)
