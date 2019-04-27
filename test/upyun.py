# -*- coding: UTF-8 -*-
import base64
import datetime
import hashlib
import hmac
import requests

# Tip 1
# 使用时需要根据自己配置与需求提供参数 key secret uri method
key = 'fondoger'
secret = '97eef486892c0b66f08a3228ebf676a3'
#secret = hashlib.md5('操作员密码'.encode()).hexdigest()


def httpdate_rfc1123(dt=None):
    dt = dt or datetime.datetime.utcnow()
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

def sign(client_key, client_secret, method, uri, date, policy=None, md5=None):
    # Tip 4
    # MD5 信息可选
    signarr = []
    for v in [method, uri, date, policy, md5]:
        if v != None:
            signarr.append(v)
    signstr = '&'.join(signarr)
    signstr = base64.b64encode(
        hmac.new(client_secret.encode(), signstr.encode(),
                 digestmod=hashlib.sha1).digest()
    ).decode()
    return 'UPYUN %s:%s' % (client_key, signstr)

def main():
    file = None
    with open(r'E:\MyDesktop\default_avatar_female_50.gif', 'rb') as f:
        file = f.read()
    fileMd5 = hashlib.md5(file).hexdigest()
    date = httpdate_rfc1123()
    uri = '/image-upyun-9527/3.webp'
    method = 'PUT'
    headers = {
        'Authorization': sign(key, secret, method, uri, date),
        'Date': date,
        'Content-Length': str(len(file)),
        'x-gmkerl-thumb': '/format/webp/quality/85/progressive/true/strip/true'
    }
    print(headers)
    from requests import Session, Request
    s = Session()
    prepped = Request(method, 'http://v0.api.upyun.com'+uri).prepare()
    prepped.headers = headers
    prepped.body = file
    r = s.send(prepped)
    print(r.status_code, r.text)

if __name__ == '__main__':
    main()