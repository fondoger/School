import requests
import json
from flask import request, current_app, jsonify
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import api
from .errors import BadRequestError
from .. import db
from ..models import User

''' 微信登陆接口
    用code换取用户的唯一标识（openid） 及本次登录的 会话密钥（session_key）等
    微信接口地址:
        https://api.weixin.qq.com/sns/jscode2session?appid=APPID&secret=SECRET&js_code=JSCODE&grant_type=authorization_code
        其中jscode是客户端发送过来的, appid和secret是小程序申请的, grant_type固定为authorization_code
    返回参数 openid, session_key, uinionid(可选)
'''


WX_APPID = 'wxb6aa7c81f96a2c48'
WX_APP_SECRET = '894f0bcbd7840a5b06f63c7c119d4c9d'
def wx_code2openid(code):
    APIURL = (('https://api.weixin.qq.com/sns/jscode2session'
             '?appid=%s&secret=%s&js_code=%s&grant_type=authorization_code')
             % (WX_APPID, WX_APP_SECRET, code))
    r = None
    try:
        r = requests.get(APIURL, timeout=2)
    except:
        raise BadRequestError('服务器无法连接微信后台')
    json_object = json.loads(r.content)
    if 'openid' not in json_object:
        raise BadRequestError("Code无效")
    return json_object['openid']


@api.route('/wechat-token', methods=['POST'])
def wechat_token():
    ''' POST json格式
        json = {
            'code':
            'wx_nickname':
            'wx_avatar':
            'wx_gender':
        }

        返回 json格式
        json = {
            'token': 
        }
    '''
    print(request.json)
    code = request.json.get('code')
    openid = wx_code2openid(code)
    user = User.query.filter_by(wx_openid=openid).first()
    if user == None:
        print('新用户')
        if 'wx_nickname' not in request.json:
            raise BadRequestError('无法获取微信个人信息')
        nickname = request.json.get('wx_nickname')
        avatar = request.json.get('wx_avatar')
        gender = request.json.get('wx_gender')
        user = User.query.filter_by(username=nickname)
        count = 0
        while user != None:
            count = count + 1
            user = User.query.filter_by(username=nickname+str(count)).first()
        print(openid, nickname+str(count), avatar, gender)
        user = User(wx_openid=openid, username=nickname+str(count), avatar=avatar, gender=gender)
        db.session.add(user)
        db.session.commit()
    token = generate_wechat_token(user)
    return jsonify(token=token)


def generate_wechat_token(user):
    s = Serializer('wechat_login'+current_app.config['SECRET_KEY'], expires_in=3600*24*7)
    playload = {
        'openid': user.wx_openid
    }
    return s.dumps(playload).decode('ascii')


def verify_wechat_token(user, token):
    '''Returns user.wx_openid'''
    s = Serializer('wechat_login'+current_app.config['SECRET_KEY'])
    try:
        s.loads(token)
    except:
        return None
    return s['openid']