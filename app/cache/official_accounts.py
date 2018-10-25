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



def _cache_account_subscribers(id: IntLike):
    key = Keys.official_account_subscribers.format(id)
    sql = """
    select users_id from subscriptions
    where official_account_id=:OID
    """
    result = db.engine.execute(text(sql), OID=id)
    subscriber_ids = [ row[0] for row in result ]
    subscriber_ids.append(-1)
    rd.sadd(key, *subscriber_ids)
    rd.expire(key, Keys.official_account_subscribers_expire)

def is_account_followed_by(id: IntLike, user_id: IntLike) -> bool:
    key = Keys.official_account_subscribers.format(id)
    if not rd.exists(key):
        _cache_account_subscribers(id)
    return rd.sismember(key, user_id)

def cache_account_json(account_json):
    """ Cache unprocessed account_json to redis """
    key = Keys.official_account_json.format(account_json['id'])
    rd.hmset(key, account_json)
    rd.expire(key, Keys.official_account_json_expire)

def get_official_account_json(id: IntLike):
    """
    Get official_account_json from redis by id
    None is returned in case of not found
    """
    key = Keys.official_account_json.format(id)
    data = rd.hgetall(key)
    json_account = None
    if not data:
        json_account = {
            'id': int(data[b'id']),
            'avatar': data[b'avatar'].decode(),
            'accountname': data[b'accountname'].decode(),
            'description': data[b'description'].decode(),
            'page_url': data[b'page_url'].decode(),
            'articles': int(data[b'articles']),
            'subscribers': int(data[b'subscribers']),
        }
        rd.expire(key, Keys.official_account_json_expire)
        return OfficialAccount.process_json(result)
    account = OfficialAccount.query.get(id)
    if account == None:
        return None
    resule = account.to_json(cache=True)
    cache_account_json(result)
    return OfficialAccount.process_json(result)





