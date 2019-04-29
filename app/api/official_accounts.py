from flask import request, g, jsonify
from . import api
from sqlalchemy.sql import text
from .utils import login_required
from .errors import forbidden, bad_request
from .. import db
from ..models import *
import app.cache as Cache
from app.utils.logger import logtimeusage


@api.route('/article', methods=['GET'])
@logtimeusage
def get_article():
    """
    1. 通过id获取某篇文章
    2. 通过official_account_id获取若干个文章
    3. 通过type=subsription获取关注的公众号所有文章
    4. 通过type=all获取所有文章
    其他参数:
        limit
        offset
    """
    id = request.args.get('id', -1, type=int)
    account_id = request.args.get('official_account_id', -1, type=int)
    type = request.args.get('type', '')
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    if id != -1:
        article = Article.query.get_or_404(id)
        return jsonify(article.to_json())
    if account_id != -1:
        articles = Article.query.filter_by(
            official_account_id=account_id)
        articles = articles.offset(offset).limit(limit)
        articles = [a.to_json() for a in articles]
        return jsonify(articles)
    if type == 'all':
        articles = Article.query.order_by(Article.timestamp)
        articles = articles.offset(offset).limit(limit)
        articles = [a.to_json() for a in articles]
        return jsonify(articles)
    if type == 'subscription':
        if not hasattr(g, 'user'):
            return forbidden("Please log in")
        sql = """select id
        from articles where official_account_id in (
            select official_account_id from subscriptions as S
            where S.users_id=:UID
        ) order by timestamp DESC limit :LIMIT offset :OFFSET;
        """
        result = db.engine.execute(text(sql), UID=g.user.id,
                                   LIMIT=limit, OFFSET=offset)
        result = list(result)
        article_ids = [item['id'] for item in result]
        articles = Cache.multiget_article_json(article_ids)
        res_map = {}
        for a in articles:
            res_map[a['id']] = a
        res = [res_map[id] for id in article_ids]
        return jsonify(res)

    return bad_request('参数有误')


@api.route('/official_account', methods=['GET'])
def get_official_account():
    """
    1. 通过id获取某个订阅号
    2. 通过type=all获取若干个订阅号
    """
    id = request.args.get('id', -1, type=int)
    type = request.args.get('type', '')
    if id != -1:
        account = OfficialAccount.query.get_or_404(id)
        return jsonify(account.to_json())
    if type == 'all':
        accounts = [a.to_json() for a in OfficialAccount.query]
        return jsonify(accounts)
    return bad_request('参数有误')


@api.route('/official_account/subscription', methods=['POST'])
@login_required
def create_official_account_subscription():
    id = request.json.get('id', -1)
    official_account = OfficialAccount.query.get_or_404(id)
    if g.user in official_account.subscribers:
        return jsonify({'message': 'already subscribed'})
    official_account.subscribers.append(g.user)
    db.session.add(official_account)
    db.session.commit()
    return jsonify({'message': 'subscribe success'})


@api.route('/official_account/subscription', methods=['DELETE'])
@login_required
def delete_official_account_subscription():
    id = request.args.get('id', -1)
    official_account = OfficialAccount.query.get_or_404(id)
    if g.user not in official_account.subscribers:
        return jsonify({'message': 'already unsubscribed'})
    official_account.subscribers.remove(g.user)
    db.session.commit()
    return jsonify({'message': 'unsubscribe success'})
