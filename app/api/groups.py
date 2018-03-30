from flask import request, g, jsonify, url_for
from . import api
from .utils import login_required, json_required
from .errors import forbidden, unauthorized, bad_request, not_found
from .. import db
from ..models import User, Group, GroupMembership, Activity

@api.route('/group', methods=['POST'])
@json_required
@login_required
def create_group():
    """
    创建团体
    json = {
        "groupname": 团体名称
        'avatar': 
    }
    """
    groupname = request.json.get('groupname', '')

    if groupname == '':
        return bad_request('groupname empty')
    group = Group.query.filter(groupname=groupname).first()
    if group is not None:
        return bad_request('groupname exists')
    group = Group(groupname=groupname)
    db.session.add(group)
    m = GroupMembership(user=g.user, group=group)
    db.session.add(m)
    db.session.commit()
    return jsonify(group.to_json()), 201, \
        {'Location': url_for('api.get_group', id=group.id, _external=True)}


@api.route('/group', methods=['GET'])
def get_group():
    """
    1. 通过id获取某个团体
    2. 通过user_id获取用户参加的团体
    2. 通过category获取团体
    3. 通过type=hot获取5个热门普通团体
    4. 通过type=new获取5个最新普通团体
    5. 通过type=public获取5个热门公开团体
    """
    id = request.args.get('id', -1, type=int)
    category = request.args.get('category', "")
    type = request.args.get('type', "")
    if id != -1:
        group = Group.query.get(id)
        if group is None:
            return not_found('找不到该团体')
        return jsonify(group.to_json())

    if category != "":
        groups = Group.query.filter_by(category='category')
        json = [group.to_json() for group in groups]
        return jsonify(json)

    if type == "hot":
        groups = Group.query.filter_by(public=False)
        groups = groups.order_by(Group.id)[:6]
        json = [group.to_json() for group in groups]
        return jsonify(json)

    if type == "new":
        groups = Group.query.filter_by(public=False)
        groups = groups.order_by(Group.id.desc())[:6]
        json = [group.to_json() for group in groups]
        return jsonify(json)

    if type == "public":
        groups = Group.query.filter_by(public=True)
        groups = groups.order_by(Group.id)[:6]
        json = [group.to_json() for group in groups]
        return jsonify(json)

    return bad_request('参数有误')


@api.route('/group', methods=['DELETE'])
@login_required
def delete_group():
    id = request.args.get('id', -1, type=int)
    if id == -1:
        return bad_request('id empty')
    group = Group.query.get(id)
    if group is None:
        return not_found('找不到该团体')
    if group.get_owner() != g.user:
        return forbidden('Only group owner can do this.')
    db.session.delete(group)
    db.session.commit()
    return jsonify({'id':id, 'message': 'delete success'})


# @api.route('/group/status', methods=['POST'])
# @json_required
# @login_required
# def create_group_status

@api.route('/activity', methods=['POST'])
@json_required
@login_required
def create_activity():
    """
    json = {
        "group_id": 团体id,
        "title": 活动名称,
        "description": 活动介绍
        "picture": 活动图片, 可选
        "keyword": 活动关键字, 提供话题
    }
    """
    group_id = request.json.get('group_id', -1)
    title = request.json.get('title', "")
    description = request.json.get('description', "")
    picture = request.json.get('picture', None)
    keyword = request.json.get('keyword', '')

    if group_id == -1:
        return bad_request('id empty')
    if title == "":
        return bad_request('title empty')
    if keyword == "":
        return bad_request('keyword emtpy')
    group = Group.query.get(group_id)
    if group is None:
        return not_found('找不到该团体')
    if group.get_owner() != g.user:
        return forbidden('Only group owner can do this')
    a = Activity(group=group, title=title, keyword=keyword,
                 description=description, picture=picture)
    db.session.add(a)
    db.session.commit()
    return jsonify(a.to_json()), 201, \
        {'Location': url_for('api.get_activity', id=a.id, _external=True)}


@api.route('/activity', methods=['GET'])
def get_activity():
    """ 获取活动
    1. 根据Activity id获取单个活动
       参数: id
    2. 获取团体发布的活动(时间序)
       参数: group_id, offset可选, default=0
    3. 获取活动(热门序), 
       参数: type=hot, offset可选, default=0
    """
    # 1.
    id = request.args.get('id', -1, type=int)
    group_id = request.args.get('group_id', -1, type=int)
    type = request.args.get('type', None)
    offset = request.args.get('offset', 0, type=int)

    if id != -1:
        a = Activity.query.get(id)
        if a is None:
            return not_found('找不到该活动')
        return jsonify(a.to_json())
    
    # 2.
    if group_id != -1:
        group = Group.query.get(group_id)
        if group is None:
            return not_found('找不到该团体')
        activities = group.activities.order_by(Activity.timestamp.desc())
        activities = activities.offset(offset).limit(5);
        json = [a.to_json() for a in activities]
        return jsonify(json)

    # 3.
    if type == 'hot':
        activities = Activity.query.order_by(Activity.timestamp.desc())
        activities = activities.offset(offset).limit(5);
        json = [a.to_json() for a in activities]
        return jsonify(json)

    return bad_request('参数有误')


@api.route('/activity', methods=['DELETE'])
@login_required
def delete_activity():
    id = request.args.get('id', -1, type=int)
    if id == -1:
        return ('id empty')
    a = Activity.query.get(id)
    if id is None:
        return ('找不到该活动')
    db.session.delete(a)
    db.session.commit()
    return jsonify({'id': id, 'message': 'delete success'})
