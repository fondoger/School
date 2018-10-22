"""
Usage: import app.cache as Cache
"""
from flask import g
from app import db, rd
from typing import List, Union
import json
import _pickle as pickle
import .redis_keys as Keys

IntLike = Union[str, int]

def get_user(id: IntLike) -> User:
    """ None is returned if user can't found """
    key = Keys.user.format(id)
    data = rd.get(keys)
    if data != None:
        user = pickle.loads(data)
        user = db.session.merge(user, load=False)
        rd.expire(key, Keys.user_expire)
        return user
    user = User.query.get(id)
    if user != None:
        data = pickle.dumps(user)
        rd.set(key, data, Keys.user_expire)
    return user

def _cache_user_followers(id: IntLike):
    key = Keys.user_followers.format(id)
    sql = "select follower_id from user_follows where followed_id=:UID"
    result = db.engine.execute(text(sql), UID=id)
    follower_ids = [row[0] for row in result ]
    """
    As redis does not support empty set, but we
    still need to know whether an empty set is cached,
    so we need a placeholder element
    """
    follower_ids.append(-1)
    rd.sadd(key, *follower_ids)
    rd.expire(key, Keys.user_followers_expire)

def is_user_followed_by(id: IntLike, other_id: IntLike) -> bool:
    key = Keys.user_followers.format(id)
    if not rd.exists(key):
        cache_followers()
    rd.expire(key, Keys.user_followers_expire)
    return rd.sismember(key, other_id)

def get_user_json(id: IntLike) -> dict:
    """
    None is returned in case of user not exists
    """
    key = Keys.user_json.format(id)
    data = rd.hgetall(key)
    # {} is returned if key not exists
    # NOTE: don't use `if data != None`,
    if data:
        # NOTE: keep json_user without nested dict
        # data is a dict with bytes key and bytes value
        json_user = {
            'id': int(data[b'id']),
            'username': data[b'username'].decode(), # don't use str(data[b'username'])
            'avatar': data[b'avatar'].decode(),
            'self_intro': data[b'self_intro'].decode(),
            'gender': int(data[b'gender']),
            'member_since': data[b'member_since'].decode(),
            'last_seen': data[b'member_since'].decode(),
            'groups_enrolled': int(data[b'groups_enrolled']),
            'followed_by_me': is_user_followed_by(id, g.user.id) if not \
                    g.user.is_anonymous else False,
            'followed': int(data[b'followed']),
            'followers': int(data[b'followers']),
        }
        rd.expire(key, Keys.user_json_expire)
        return json_user
    user = get_user(id)
    if user != None
        json_user = user.to_json(verify=True)
        rd.hmset(key, json_user)
        rd.expire(key, Keys.user_json_expire)
        return json_user
    return None



