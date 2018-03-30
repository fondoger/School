from flask import request, g, jsonify, url_for
from datetime import datetime
from . import api
from .utils import login_required, json_required
from .errors import forbidden, unauthorized, bad_request, not_found
from .. import db
from ..models import User, Sale, SalePicture, SaleComment


@api.route('/sale', methods=['POST'])
@json_required
@login_required
def create_sale():
    title = request.json.get('title', '')
    text = request.json.get('text', '')
    pics = request.json.get('pics', [])
    price = request.json.get('price', 0.0)
    location = request.json.get('location', '')
    category = request.json.get('category', '')
    if title == '':
        return bad_request('title empty')
    if text == '':
        return bad_request('text empty')
    if len(pics) == 0:
        return bad_request(('image empty'))
    if location not in Sale.LOCATION:
        return bad_request('location error')
    if category not in Sale.CATEGORY:
        return bad_request('category error')
    s = Sale(user=g.user, title=title, text=text, price=price, 
             location=location, category=category)
    for index, pic_url in enumerate(pics):
        p = SalePicture(url=pic_url, sale=s, index=index)
        db.session.add(p)
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_json()), 201, \
        {'Location': url_for('api.get_sale', id=s.id, _external=True)}


@api.route('/sale', methods=['GET'])
def get_sale():
    id = request.args.get('id', -1, type=int)
    user_id = request.args.get('user_id', -1)
    location = request.args.get('location', 'all')
    category = request.args.get('category', 'all')
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)

    if id != -1:
        s = Sale.query.get_or_404(id)
        return jsonify(s.to_json())

    sales = Sale.query
    if user_id != -1:
        u = User.query.get_or_404(user_id)
        sales = sales.filter_by(user=u)
    if location != 'all':
        sales = sales.filter_by(location=location)
    if category != 'all':
        sales = sales.filter_by(category=category)

    sales = sales.order_by(Sale.updated_at.desc())
    sales = sales.offset(offset).limit(limit)
    sales = [s.to_json() for s in sales]
    return jsonify(sales)

@api.route('/sale', methods=['PUT', 'PATCH'])
@json_required
@login_required
def update_sale():
    id = request.json.get('id', -1)
    s = Sale.query.get_or_404(id)
    if s.user != g.user:
        return forbidden('owner required')
    s.updated_at = datetime.utcnow()
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_json()), 201, \
        {'Location': url_for('api.get_sale', id=s.id, _external=True)}


@api.route('/sale', methods=['DELETE'])
@login_required
def delete_sale():
    """ 删除微博, 成功返回删除的id """
    id = request.args.get('id', -1, type=int)
    s = Sale.query.get_or_404(id)
    if s.user != g.user:
        return forbidden('owner required')
    db.session.delete(s)
    db.session.commit()
    return jsonify({'id': id, 'message': 'delete success'})


@api.route('/sale/like', methods=['POST'])
@json_required
@login_required
def create_sale_like():
    sale_id = request.json.get('sale_id', -1)
    s = Sale.query.get_or_404(sale_id)
    if g.user in s.liked_users:
        return jsonify({'sale_id': sale_id, 'message': 'already created.'})
    s.liked_users.append(g.user)
    db.session.add(s)
    db.session.commit()
    return jsonify({'sale_id': sale_id, 'message': 'create success'})


@api.route('/sale/like', methods=['DELETE'])
@login_required
def delete_sale_like():
    sale_id = request.args.get('sale_id', -1, type=int)
    s = Sale.query.get_or_404(sale_id)
    if g.user not in s.liked_users:
        return jsonify({'sale_id': sale_id, 'message': 'already deleted.'})
    s.liked_users.remove(g.user)
    db.session.add(s)
    db.session.commit()
    return jsonify({'sale_id': sale_id, 'message': 'delete success'})


@api.route('/sale/comment', methods=['POST'])
@json_required
@login_required
def create_sale_comment():
    sale_id = request.json.get('sale_id', -1)
    text = request.json.get('text', '')
    s = Sale.query.get_or_404(sale_id)
    if text == '':
        return bad_request('text empty')
    c = SaleComment(text=text, sale=s, user=g.user)
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_json()), 201, \
        {'Location': url_for('api.get_sale_comment', id=c.id, _external=True)}


@api.route('/sale/comment', methods=['GET'])
def get_sale_comment():
    id = request.args.get('id', -1, type=int)
    sale_id = request.args.get('sale_id', -1, type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    if id != -1:
        c = SaleComment.query.get_or_404(id)
        return jsonify(c.to_json())
    s = Sale.query.get_or_404(sale_id)
    comments = s.comments.order_by(SaleComment.timestamp.desc())
    comments = s.comments.offset(offset).limit(limit)
    comments = [c.to_json() for c in comments]
    return jsonify(comments)


@api.route('/sale/comment', methods=['DELETE'])
@login_required
def delete_sale_comment():
    id = request.args.get('id', -1, type=int)
    c = SaleComment.query.get_or_404(id)
    if c.user != g.user:
        return forbidden('owner required')
    db.session.delete(c)
    db.session.commit()
    return jsonify({'id': id, 'message': 'delete success'})