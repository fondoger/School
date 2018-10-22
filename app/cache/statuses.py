"""
Usage: import app.cache as Cache
"""
from flask import g
from app import db, rd
from sqlalchemy.sql import text
from typing import List, Union
import json
import _pickle as pickle
from .users import get_user_json
from . import redis_keys as Keys
from app.utils.logger import logfuncall

IntLike = Union[int, str]

def get_status(id: IntLike) -> 'Status':
    """
    get status by id
    none is returned in case of status not found
    """
    key = Keys.status.format(id)
    data = rd.get(key)
    if data != None:
        status = pickle.loads(data)
        status = db.session.merge(status, load=False)
        rd.expire(status, Keys.status_expire)
        return status
    status = Status.query.get(id)
    if status != None:
        data = pickle.dumps(status)
        rd.set(key, data, Keys.status_expire)
    return status

def get_statuses(ids: List[IntLike]) -> List['Status']:
    """
    get multiple statuses by ids
    result may not have same length of `ids` and
    may not returned in their's orignal order
    """
    statuses = []
    missed_ids = []
    # get from redis cache
    for index, id in enumerate(ids):
        key = Keys.status.format(id)
        data = rd.get(key)
        if data != None:
            status = pickle.loads(data)
            status = db.session.merge(status, load=False)
            statuses.append(status)
            rd.expire(key, Keys.status_expire)
        else:
            missed_ids.append(id)
    # get from mysql
    missed_statuses = Status.query.filter(Status.id.in_(missed_ids)).all()
    for s in missed_statuses:
        statuses.append(s)
        key = Keys.status.format(id)
        data = pickle.dumps(status)
        rd.set(key, data, Keys.status_expire)
    return statuses

def _cache_liked_users(id: IntLike):
    key = Keys.status_liked_users.format(id)
    sql = 'select user_id from status_likes where status_id=:SID'
    result = db.engine.execute(text(sql), SID=id)
    liked_user_ids = [ row[0] for row in result ]
    liked_user_ids.append(-1)
    rd.sadd(key, *liked_user_ids)
    rd.expire(key, Keys.status_liked_users_expire)

def is_status_liked_by(id: IntLike, other_id: IntLike) -> bool:
    key = Keys.status_liked_users.format(id)
    if not rd.exists(key):
        _cache_liked_users(id)
    return rd.sismember(key, other_id)

@logfuncall
def get_status_json(id: IntLike) -> dict:
    """
    None is returned in case of status is not found
    """
    key = Keys.status_json.format(id)
    data = rd.hgetall(key)
    result = None
    # data is a dict with bytes key and bytes value
    if data:
        result = {
            'id': int(data[b'id']),
            'type': data[b'type'].decode(),
            'title': data[b'title'].decode(),
            'text': data[b'text'].decode(),
            'timestamp': data[b'timestamp'].decode(),
            'replies': int(data[b'replies']),
            'likes': int(data[b'likes']),
            'pics': json.loads(data[b'pics_json'].decode()),
            'user_id': data[b'user_id'].decode(),
            'group_id': data[b'group_id'].decode(),
        }
    else:
        status = get_status(id)
        if status == None:
            return None
        result = status.to_json(cache=True)
        result['pics_json'] = json.dumps(result['pics'],
                ensure_ascii=False)
        rd.hmset(key, result)

    result['user'] = get_user_json(result['user_id'])
    result['liked_by_me'] = is_status_liked_by(id, g.user.id) if \
            not g.user.is_anonymous else False
    if result['type'] == 'GROUP_STATUS' or \
            result['type'] == 'GROUP_POST':
        print("Using Cache.get_group instead of Group.query")
        group = Group.query.get(result['group_id'])
        result['group'] = group.to_json()
    if result['type'] == 'GROUP_STATUS':
        result['group_user_title'] = 'Title(TODO)'
    # remove useless keys
    result.pop('pics_json', None)
    result.pop('user_id', None)
    result.pop('group_id', None)
    rd.expire(key, Keys.status_json_expire)
    return result



from app.models import *





