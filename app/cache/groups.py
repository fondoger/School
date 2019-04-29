"""
Usage: import app.cache as Cache
"""
from app import db, rd
from sqlalchemy.sql import text
from typing import Union
import json
from . import redis_keys as KEYS
from app.models import Group

IntLike = Union[int, str]


def get_group_user_title(group_id: IntLike, user_id: IntLike):
    """
    Get user's title in some group
    "" is returned if not found
    """
    key = KEYS.group_user_title.format(group_id=group_id, user_id=user_id)
    data = rd.get(key)
    if data is not None:
        rd.expire(key, KEYS.group_user_title_expire)
        return data.decode()
    sql = """
    select title from group_memberships
    where user_id=:UID and group_id=:GID
    """
    result = db.engine.execute(text(sql), UID=user_id, GID=group_id)
    res = result.first()
    if res is None:
        return ""
    title = res[0]
    rd.set(key, title, ex=KEYS.group_user_title_expire)
    return title


def cache_group_json(group_json):
    """ Cache group_json to redis """
    key = KEYS.group_json.format(group_json['id'])
    data = json.dumps(group_json, ensure_ascii=False)
    rd.set(key, data, ex=KEYS.group_json_expire)


def get_group_josn(id: IntLike):
    """
    Get group json from redis
    None is returned in case of not found
    """
    key = KEYS.group_json.format(id)
    data = rd.get(key)
    if data is not None:
        json_group = json.loads(data.decode())
        rd.expire(key, KEYS.group_json_expire)
        return Group.process_json(json_group)
    group = Group.query.get(id)
    if group is None:
        return None
    json_group = group.to_json(cache=True)
    cache_group_json(json_group)
    return Group.process_json(json_group)
