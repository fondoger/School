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
from app.models import User, Status

IntLike = Union[int, str]

def get_status(id: IntLike) -> 'Status':
    """
    Get status instance by id
    None is returned in case of status not found
    """
    key = Keys.status.format(id)
    data = rd.get(key)
    if data != None:
        status = pickle.loads(data)
        status = db.session.merge(status, load=False)
        rd.expire(key, Keys.status_expire)
        return status
    status = Status.query.get(id)
    if status != None:
        data = pickle.dumps(status)
        rd.set(key, data, Keys.status_expire)
    return status


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

def cache_status_json(status_json):
    """ Cache unprocessed status_json to redis """
    key = Keys.status_json.format(status_json['id'])
    rd.hmset(key, status_json)
    rd.expire(key, Keys.status_json_expire)

@logfuncall
def get_status_json(id: IntLike, only_from_cache=False) -> dict:
    """
    Return processed status_json
    None is returned in case of status is not found
    """
    key = Keys.status_json.format(id)
    data = rd.hgetall(key)
    result = None
    # data is a dict with bytes key and bytes value
    if data:    # hit in redis cache
        result = {
            'id': int(data[b'id']),
            'type': data[b'type'].decode(),
            'title': data[b'title'].decode(),
            'text': data[b'text'].decode(),
            'timestamp': data[b'timestamp'].decode(),
            'replies': int(data[b'replies']),
            'likes': int(data[b'likes']),
            'user_id': data[b'user_id'].decode(),
            'group_id': data[b'group_id'].decode(),
            'pics_json': data[b'pics_json'].decode()
        }
        rd.expire(key, Keys.status_json_expire)
        return Status.process_json(result)
    if only_from_cache:
        return None
    status = get_status(id)
    if status == None:
        return None
    result = status.to_json(cache=True)
    cache_status_json(result)
    return Status.process_json(result)

@logfuncall
def multiget_status_json(ids: List[IntLike]) -> List['Status']:
    """
    get multiple statuses by ids
    result may not have same length of `ids` and
    may not returned in their's orignal order
    """
    statuses = []
    missed_ids = []
    # get from redis cache
    for index, id in enumerate(ids):
        status_json = get_status_json(id, only_from_cache=True)
        if status_json != None:
            statuses.append(status_json)
        else:
            missed_ids.append(id)
    if not missed_ids:
        return statuses
    # get from mysql
    missed_statuses = Status.query.filter(Status.id.in_(missed_ids)).all()
    for s in missed_statuses:
        status_json = s.to_json(cache=True)
        cache_status_json(status_json)
        statuses.append(Status.process_json(status_json))
    return statuses






