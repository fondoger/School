"""
Usage: import app.cache as Cache
"""
from flask import g
from app import db, rd
from sqlalchemy.sql import text
from typing import List, Union
import json
import _pickle as pickle
from . import redis_keys as Keys
from app.utils.logger import logfuncall
from app.models import User, Status, Group

IntLike = Union[int, str]


def get_group_user_title(group_id: IntLike, user_id: IntLike):
    """
    Get user's title in some group
    "" is returned if not found
    """
    key = Keys.group_user_title.format(group_id=group_id,
            user_id=user_id)
    data = rd.get(key)
    if data != None:
        rd.expire(key, Keys.group_user_title_expire)
        return data.decode()
    sql = """
    select title from group_memberships
    where user_id=:UID and group_id=:GID
    """
    result = db.engine.execute(text(sql), UID=user_id, GID=group_id)
    res = result.first()
    if res == None:
        return ""
    title = res[0]
    rd.set(key, title, ex=Keys.group_user_title_expire)
    return title

def cache_group_josn(group_json):
    """ Cache group_json to redis """
    key = Keys.group_json.format(group_json['id'])
    data = json.dumps(group_json, ensure_ascii=False)
    rd.set(key, data, ex=Keys.group_json_expire)

def get_group_josn(id: IntLike):
    """
    Get group json from redis
    None is returned in case of not found
    """
    key = Keys.group_json.format(id)
    data = rd.get(key)
    json_group = None
    if data != None:
        json_group = josn.loads(data.decode())
        rd.expire(key, Key.group_json_expire)
        return Group.process_json(json_group)
    group = Group.query.get(id)
    if group == None:
        return None
    josn_group = group.to_json(cache=True)
    cache_group_json(json_group)
    return Group.process_json(json_group)



















