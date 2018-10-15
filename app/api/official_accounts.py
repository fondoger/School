from flask import request, g, jsonify
from . import api
from .utils import login_required, json_required
from .errors import forbidden, unauthorized, bad_request, not_found
from .. import db
from ..models import *


@api.route('/official_account', methods=['GET'])
def get_official_account():
    """
    1. 通过id获取某个订阅号
    2. 通过type=all获取若干个订阅号
    """
    id = request.args.get('id', -1, type=int)
    type = request.args.get('type', '')
    if id != -1:
        account = OfficialAccount.query.get(id)
        if account is None:
            return not_found('找不到该订阅号')
        return jsonify(account.to_json())
    if type == 'all':
        accounts = [a.to_json() for a in OfficialAccount.query]
        return jsonify(accounts)
    return bad_request('参数有误')

@api.route('/official_account/subscription', methods=['POST'])
@login_required
def create_official_account_subscription():
    id = request.json.get('id', -1)
    official_account = OfficialAccount.query.get(id)
    if official_account is None:
        return not_found('找不到该订阅号')
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
    official_account = OfficialAccount.query.get(id)
    if official_account is None:
        return not_found('找不到该订阅号')
    if g.user not in official_account.subscribers:
        return jsonify({'message': 'already unsubscribed'})
    official_account.subscribers.remove(g.user)
    db.session.commit()
    return jsonify({'message': 'unsubscribe success'})







