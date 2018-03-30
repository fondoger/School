import re
import json
from flask import jsonify, g, request
from . import api
from .. import db
from ..models import WaitingUser, User, TempImage
from .utils import json_required
from .aliyun_mail import AliyunEmail
from .errors import forbidden, unauthorized, bad_request, not_found, internal_error

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
# 4-30个字符，支持中英文、数字、"_"或减号, 一个中文相当于两个英文字符
USERNAME_REGEX = re.compile(r"^[\u4e00-\u9fa5_a-zA-Z0-9\-]{2,30}$")
CHINESE_CHARACTER = re.compile(r"[\u4e00-\u9fa5]")
# 最少8位数, 最少含有1个数子和1个字母
PASSWORD_REGEX = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$") 
aliyun = AliyunEmail()

def getUsernameLength(username):
    strLength = len(username)
    strLength += len(CHINESE_CHARACTER.findall(username))
    return strLength

@api.route('/verification_code', methods=['POST'])
@json_required
def send_verification_code():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    # check for valid email address
    if not EMAIL_REGEX.match(email):
        return bad_request('email invalid')
    if not PASSWORD_REGEX.match(password):
        return bad_request('password invalid')
    # if (not USERNAME_REGEX.match(username) or not
    #     (4 <= getUsernameLength(username) <= 30)):
    #     return bad_request('username invalid')
    # check for duplication
    if User.query.filter_by(email=email).first() is not None:
        return bad_request('email exists')

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


@api.route('/activation', methods=['POST'])
@json_required
def activate_user():
    email = request.json.get('email', '')
    verification_code = request.json.get('verification_code', '')

    wu = WaitingUser.verify(email, verification_code)
    if wu is not None:
        u = User(email=wu.email, username=wu.username, 
                 password_hash=wu.password_hash)
        db.session.add(u)
        db.session.delete(wu)
        db.session.commit()
        return jsonify({'user':u.to_json(), 'token': u.generate_auth_token(
                       expiration=3600*24*365), 'expiration': 3600*24*365})
    return bad_request('verify_code error')


@api.route('/update', methods=['GET'])
def get_updage_info():
    platform = request.args.get('platform', '')
    if platform == 'ios':
        return "haha"
    if platform == 'android':
        json = {
            "version": "1.0.1",
            "description": "更新功能测试",
            "download_url": None,
        }
        return jsonify(json)
    return bad_request('please specify a platform(ios/android)')


@api.route('/upyun-notify-url', methods=['POST'])
def receive_image_notify():
    # todo, check signature for security
    # http://47.93.240.135/api/v1
    url = request.form.get('url')
    width = int(request.form.get('image-width'))
    height = int(request.form.get('image-height'))
    type = request.form.get('image-type')
    colors = request.form.get('theme_color')
    theme_color = json.loads(colors)[0]['color']
    time = int(request.form.get('time'))
    image = TempImage(url=url, width=width, height=height, type=type,
                      theme_color=theme_color, time=time)
    db.session.add(image)
    db.session.commit()
    return ''

    

