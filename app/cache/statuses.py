"""
Usage: import app.cache as Cache
"""
from flask import g
from app import db, rd
from typing import List, Union
import json
import _pickle as pickle
import .redis_keys as Keys
import . as Cache

IntLike = Union[int, str]

def get_status(id: IntLike) -> Status:
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

def get_statuses(ids: List[IntLike]) -> List[Status]:
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


def get_status_json(id: IntLike) -> dict:
    """
    None is returned in case of status is not found
    """
    key = Keys.status_json.format(id)
    data = rd.hgetall(key)
    # data is a dict with bytes key and bytes value
    if data:
        json_status = {
            'id': int(data[b'id']),
            'type': data[b'type'].decode(),
            'title': data[b'title'].decode(),
            'text': data[b'text'].decode(),
            'user': Cache.get_user(int(data[b'user_id']))
        }







