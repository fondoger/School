from flask import request, g, jsonify, url_for
from . import api
from .utils import login_required, json_required
from .errors import forbidden, bad_request
from .. import db
from ..models import User, TextMessage, Message
from sqlalchemy import func


@api.route('/message', methods=['POST'])
@json_required
@login_required
def create_message():
    with_id = request.json.get('with_id', -1)
    text = request.json.get('text', '')

    if text == '':
        return bad_request('text empty')

    uto = User.query.get_or_404(with_id)

    text_message = TextMessage(ufrom_id=g.user.id, uto_id=uto.id, text=text)
    db.session.add(text_message)
    message = Message(user=uto, text_message=text_message, with_id=g.user.id)
    message_send = Message(user=g.user, text_message=text_message, with_id=uto.id, is_read=True)
    db.session.add(message)
    db.session.add(message_send)
    db.session.commit()

    return jsonify(message.to_json()), 201, \
        {'Location': url_for('api.get_message', id=message.id, _external=True)}


@api.route('/message', methods=['GET'])
@login_required
def get_message():
    """
    1. get a message by message_id
    2. get chat list without any args
    3. get a chat by uto_id
    """
    id = request.args.get('id', -1)
    with_id = request.args.get('with_id', -1)
    offset = request.args.get('offset', 0)
    limit = request.args.get('limit', 10)

    if id != -1:
        m = Message.query.get_or_404(id)
        if m.user != g.user:
            return forbidden({"owner required"})
        return jsonify(m.to_json(True))

    if with_id != -1:
        messages = g.user.messages.filter_by(with_id=with_id)
        for m in messages:
            m.is_read = True
            db.session.add(m)
        else:
            db.session.commit()
        messages = messages.offset(offset).limit(limit)
        messages = [m.to_json() for m in messages]
        return jsonify(messages)

    # Not working due to `ONLY_FULL_GROUP_BY` in mysql
    # messages = g.user.messages.order_by(Message.id.desc()).group_by(Message.with_id)
    subquery = db.session.query(func.max(Message.id)).filter_by(user_id=g.user.id)\
        .group_by(Message.with_id)
    messages = Message.query.filter(Message.id.in_(subquery)).all()
    messages = [m.to_json(True) for m in messages]
    return jsonify(messages)


@api.route('/message', methods=['PUT', 'PATCH'])
@login_required
def update_message():
    with_id = request.args.get('with_id', -1)
    messages = g.user.messages.filter_by(with_id=with_id, is_read=False)
    for m in messages:
        m.is_read = True
        db.session.add(m)
    db.session.commit()
    return jsonify({'id': id, 'message': 'update success'})


@api.route('/message', methods=['DELETE'])
@login_required
def delete_message():
    id = request.args.get('id', -1)
    with_id = request.args.get('with_id', -1)

    if id != -1:
        m = Message.query.get_or_404(id)
        if m.user != g.user:
            return forbidden('owner required')
        db.session.delete(m)
        db.session.commit()
        return jsonify({'id':id, 'message': 'delete success'})

    if with_id != -1:
        messages = g.user.messages.filter_by(with_id=with_id)
        for m in messages:
            db.session.delete(m)
        db.session.commit()
        return jsonify({'with_id': with_id, 'message': 'delete success'})

    return bad_request('invalid request')




