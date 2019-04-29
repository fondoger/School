from app import rd
from typing import List, Union
import json
from . import redis_keys as Keys
from app.utils.logger import logfuncall
from app.models import Article

IntLike = Union[str, int]


def cache_article_json(article_json):
    """ Cache article_json to redis """
    key = Keys.article_json.format(article_json['id'])
    data = json.dumps(article_json, ensure_ascii=False)
    rd.set(key, data, ex=Keys.article_json_expire)


def get_article_json(id: IntLike,
                     only_from_cache=False,
                     process_json=True) -> Union[dict, None]:
    """
    Get  article json by id

    `only_from_cache` is for multiget_article_json()
    """
    key = Keys.article_json.format(id)
    data = rd.get(key)  # none is returned if not exists
    if data is not None:
        json_article = json.loads(data.decode())
        rd.expire(key, Keys.article_json_expire)
        if not process_json:
            return json_article
        return Article.process_json(json_article)
    if only_from_cache:
        return None
    article = Article.query.get(id)
    if article is None:
        return None
    json_article = article.to_json(cache=True)
    cache_article_json(json_article)
    if not process_json:
        return json_article
    return Article.process_json(json_article)


@logfuncall
def multiget_article_json(ids: List[IntLike]) -> List['Article']:
    """
    get multiple articles by ids

    result may not have same length of `ids` and
    may not returned in their original order
    """
    articles = []
    missed_ids = []
    # get from redis cache
    for index, id in enumerate(ids):
        article_json = get_article_json(id, only_from_cache=True)
        if article_json is not None:
            articles.append(article_json)
        else:
            missed_ids.append(id)
    if not missed_ids:
        return articles
    # get from mysql
    missed_articles = Article.query.filter(Article.id.in_(missed_ids)).all()
    for a in missed_articles:
        article_json = a.to_json(cache=True)
        cache_article_json(article_json)
        articles.append(Article.process_json(article_json))
    return articles
