import re
from flask import request, current_app, jsonify, g, url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import api
from .utils import login_required, json_required
from .aliyun_mail import AliyunEmail
from .authentication import auth
from .errors import bad_request, unauthorized, forbidden, not_found, internal_error
from app import db
from app.models import *
import app.cache as Cache
import app.cache.redis_keys as Keys
from sqlalchemy import func

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
# 4-30个字符，支持中英文、数字、"_"或减号, 一个中文相当于两个英文字符
USERNAME_REGEX = re.compile(r"^[\u4e00-\u9fa5_a-zA-Z0-9\-]{2,30}$")
CHINESE_CHARACTER = re.compile(r"[\u4e00-\u9fa5]")
# 最少8位数, 最少含有1个数字和1个字母
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$")
aliyun = AliyunEmail()


@api.route('/user', methods=['GET'])
def get_user():
    ''' 根据id获取用户信息
        Note: id不存在时返回当前登录用户信息
    '''
    id = request.args.get('id', -1, type=int)
    username = request.args.get('username', '')
    keyword = request.args.get('keyword', '')
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    if id != -1:
        user = Cache.get_user(id)
        if user == None:
            return not_found("找不到该用户")
        return jsonify(user.to_json())
    if username != '':
        user = User.query.filter_by(username=username).first_or_404()
        return jsonify(user.to_json())
    if keyword != '':
        users = User.query.filter(User.username.like('%' + keyword + '%'))
        users = users.order_by(func.char_length(User.username))
        users = users.offset(offset).limit(limit)
        users = [u.to_json() for u in users]
        return jsonify(users)

    return bad_request("参数有误")


@api.route('/user', methods=['PATCH', 'PUT'])
@json_required
@login_required
def change_user():
    """
        formdata = {
            "username":  // 新用户名
            "avatar":
            "self_intro":
            "password_old":
            "password_new":
        }
        功能:
        1. 更改密码
            Note: 此前发放的所有Token强制失效.
        2. 更改头像
        3. 更改用户名
        4. 更改自我介绍
        5. 更改性别
        成功状态码201, 返回修改后的User信息
        Note: 一次请求只能更改其中的一项
    """
    password_old = request.json.get('password_old', '')
    password_new = request.json.get('password_new', '')
    avatar = request.json.get('avatar', '')
    self_intro = request.json.get('self_intro', '')
    username = request.json.get('username', '')
    gender = request.json.get('gender', -1)
    # 更改密码
    if password_old and password_new:
        errors = []
        if not g.user.verify_password(password_old):
            errors.append('password error')
        if len(password_new) <= 5 or len(password_new) >= 17:
            errors.append('password invalid')
        if len(errors) != 0:
            return bad_request(', '.join(errors))
        g.user.password = request.form['password_new']
    # 更改头像
    if avatar:
        ''' Todo:
            Should use regular expression
            Should check no any blank
        '''
        g.user.avatar = avatar

    # 更改用户名
    if username:
        strLength = len(username)
        strLength += len(CHINESE_CHARACTER.findall(username))
        if (not USERNAME_REGEX.match(username) or not
        (4 <= strLength <= 30)):
            return bad_request('username invalid')
        u = User.query.filter_by(username=username).first()
        if u == g.user:
            return bad_request('username unchanged')
        if u != None:
            return bad_request('username exists')
        g.user.username = username

    # 更改自我介绍
    if self_intro:
        g.user.self_intro = self_intro
    if gender != -1:
        if gender == 0 or gender == 1 or gender == 2:
            g.user.gender = gender
        else:
            return bad_request('gender must be 0(unknonwn), 1(male) or 2(female).')
            # g.user.gender = int(gender)
    db.session.add(g.user)
    db.session.commit()
    return jsonify(g.user.to_json()), 201, \
           {'Location': url_for('api.get_user', id=g.user.id, _external=True)}


@api.route('/user/follower', methods=['GET'])
def get_user_followers():
    id = request.args.get('id', -1, type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    user = Cache.get_user(id)
    if user is None:
        return not_found('找不到该用户')
    users = user.followers.offset(offset).limit(limit)
    users = [u.to_json() for u in users]
    return jsonify(users)


@api.route('/user/followed', methods=['GET'])
def get_user_followed():
    id = request.args.get('id', -1, type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    user = Cache.get_user(id)
    if user is None:
        return not_found('找不到该用户')
    users = user.followed.offset(offset).limit(limit)
    users = [u.to_json() for u in users]
    return jsonify(users)


@api.route('/user/followed', methods=['POST'])
@json_required
@login_required
def create_user_followed():
    id = request.json.get('id', -1)
    user = Cache.get_user(id)
    if user is None:
        return not_found('找不到该用户')
    if user == g.user:
        return bad_request('不可以关注自己哦')
    if user in g.user.followed:
        return jsonify({'message': 'already followed'})
    g.user.followed.append(user)
    db.session.add(g.user)
    db.session.commit()
    return jsonify({'message': 'followed success'})


@api.route('/user/followed', methods=['DELETE'])
@login_required
def delete_user_followed():
    id = request.args.get('id', -1, type=int)
    user = Cache.get_user(id)
    if user is None:
        return not_found('找不到该用户')
    if user not in g.user.followed:
        return jsonify({'message': 'already unfollowed'})
    g.user.followed.remove(user)
    db.session.add(g.user)
    db.session.commit()
    return jsonify({'message': 'unfollow success'})


@api.route('/user/group', methods=['GET'])
def get_user_groups():
    id = request.args.get('id', -1, type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    user = Cache.get_user(id)
    if user is None:
        return not_found('找不到该用户')
    groups = user.groups[offset:offset + limit]
    json = []
    for group in groups:
        item = group.to_json()
        item['title'] = group.get_user_title(user)
        json.append(item)
    return jsonify(json)


@api.route('/user/waiting', methods=['POST'])
@json_required
def creat_waiting_user():
    """ 缓存用户信息并发送验证码到邮箱 """

    email = request.json.get('email', '')
    password = request.json.get('password', '')

    # check for valid email address
    if not EMAIL_REGEX.match(email):
        return bad_request('email invalid')
    if not PASSWORD_REGEX.match(password):
        return bad_request('password invalid')

    if User.query.filter_by(email=email).first() is not None:
        return bad_request('该邮箱已存在')

    t = WaitingUser.query.get(email)
    if t is not None:
        db.session.delete(t)
        db.session.commit()
    wu = WaitingUser(email=email, password=password)
    db.session.add(wu)
    db.session.commit()

    if aliyun.sendActivationEmail(email, wu.verification_code):
        return jsonify({"message": "email success"})
    else:
        return internal_error("failed sending email")


def user_first_created(u):
    developer = Cache.get_user(1)
    developer.followers.append(u)
    db.session.add(u)
    for a in OfficialAccount.query:
        a.subscribers.append(u)
        db.session.add(a)


@api.route('/user', methods=['POST'])
@json_required
def create_user():
    email = request.json.get('email', '')
    verification_code = request.json.get('verification_code', -1)
    wu = WaitingUser.verify(email, verification_code)
    if wu is not None:
        u = User(email=wu.email, password_hash=wu.password_hash)
        db.session.add(u)
        db.session.delete(wu)
        user_first_created(u)
        db.session.commit()
        return jsonify({'user': u.to_json(), 'token': u.generate_auth_token(
            expiration=3600 * 24 * 365), 'expiration': 3600 * 24 * 365})
    return bad_request('verification_code error')

