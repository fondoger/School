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
def cache_status_json(status_json):
    """ Cache unprocessed status_json to redis """
    key = Keys.status_json.format(status_json['id'])
    data = json.dumps(status_json, ensure_ascii=False)
    rd.set(key, data, ex=Keys.status_json_expire)

@logfuncall
def get_status_json(id: IntLike,
        only_from_cache=False,
        process_json=True) -> dict:
    """
    Geturn processed status_json

    * None is returned in case of status is not found
    * `only_from_cache` is for multiget_status_json()
    """
    key = Keys.status_json.format(id)
    data = rd.get(key)
    result = None
    # data is a dict with bytes key and bytes value
    if data:    # hit in redis cache
        result = json.loads(data.decode())
        rd.expire(key, Keys.status_json_expire)
        if process_json:
            return Status.process_json(result)
        return result
    if only_from_cache:
        return None
    print("Can't load status {} from redis".format(id))
    print("Try to load from mysql")
    status = Status.query.get(id)
    if status == None:
        print("Can't load status {} from mysql".format(id))
        return None
    result = status.to_json(cache=True)
    cache_status_json(result)
    if process_json:
        return Status.process_json(result)
    return result

@logfuncall
def multiget_status_json(ids: List[IntLike]) -> List['Status']:
    """
    Get multiple statuses by ids

    result may not have same length of `ids` and
    may not returned in their's original order
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






