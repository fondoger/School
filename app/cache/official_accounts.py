from app import db, rd
from sqlalchemy.sql import text
from typing import Union
import json
from . import redis_keys as KEYS
from app.models import OfficialAccount

IntLike = Union[int, str]


def _cache_account_subscribers(id: IntLike):
    key = KEYS.official_account_subscribers.format(id)
    sql = """
    select users_id from subscriptions
    where official_account_id=:OID
    """
    result = db.engine.execute(text(sql), OID=id)
    subscriber_ids = [row[0] for row in result]
    subscriber_ids.append(-1)
    rd.sadd(key, *subscriber_ids)
    rd.expire(key, KEYS.official_account_subscribers_expire)


def is_account_followed_by(id: IntLike, user_id: IntLike) -> bool:
    key = KEYS.official_account_subscribers.format(id)
    if not rd.exists(key):
        _cache_account_subscribers(id)
    return rd.sismember(key, user_id)


def get_subscriber_ids(id: IntLike):
    key = KEYS.official_account_subscribers.format(id)
    ids = rd.smembers(key)
    if not ids:
        _cache_account_subscribers(id)
        ids = rd.smembers(key)
    rd.expire(key, KEYS.official_account_subscribers_expire)
    ids = [t.decode() for t in ids]
    return ids


def cache_account_json(account_json) -> None:
    """ Cache unprocessed account_json to redis """
    key = KEYS.official_account_json.format(account_json['id'])
    data = json.dumps(account_json)
    rd.set(key, data, ex=KEYS.official_account_json_expire)


def get_official_account_json(id: IntLike):
    """ Get official_account_json from redis by id

    None is returned in case of not found
    """
    key = KEYS.official_account_json.format(id)
    data = rd.get(key)
    if data is not None:
        json_account = json.loads(data.decode())
        rd.expire(key, KEYS.official_account_json_expire)
        return OfficialAccount.process_json(json_account)
    account = OfficialAccount.query.get(id)
    if account is None:
        return None
    json_account = account.to_json(cache=True)
    cache_account_json(json_account)
    return OfficialAccount.process_json(json_account)
