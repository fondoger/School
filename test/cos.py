import time
import hmac
import json
import hashlib
import urllib.parse
from requests_futures.sessions import FuturesSession
import sys
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from requests import Request, Session


class QCloudCOS(object):
    def __init__(self):
        self.SecretId = "AKIDBLLAoGm8ILD2kLg4DBxXdeUDyc5VPKUZ"
        self.SecretKey = '73ncMv9E7oJczW7XxEJH2lRwGPPDyc8P'
        self.Host = 'bucket1-1251216457.cos.ap-beijing.myqcloud.com'
        # OTHER SETTINGS
        self.AuthoizationExpireTime = 30
        self.session = FuturesSession()

    def test_get(self):
        """ COS中已经有了名为1.png的私有读写文件 """
        filename = '1.png'
        method = 'GET'
        headers = {
            'Host': self.Host,
        }
        headers.update({'Authorization': self._get_authorization(filename, headers, method)})
        s = Session()
        req = Request('GET', 'https://'+self.Host+'/'+filename)
        prepped = req.prepare()
        prepped.headers = headers
        r = s.send(prepped)
        print(r.text)

    def test_put(self):
        filename = '1.png'
        method = 'PUT'
        headers = {
            'Host': self.Host,
            'Content-Length': "10" # 文件长度很小不影响 
        }
        headers.update({'Authorization': self._get_authorization(filename, headers, method)})
        s = Session()
        req = Request(method, 'https://'+self.Host+'/'+filename)
        prepped = req.prepare()
        prepped.headers = headers
        print(headers)
        with open(filename, 'rb') as f:
            prepped.body = f.read()
        r = s.send(prepped)
        print(r.text)

    def _get_authorization(self, filename, headers, method):
        parameters = {}
        parameterKeyList = [item.lower() for item in parameters.keys()]
        parameterKeyList.sort()
        headersKeyList = [item.lower() for item in headers.keys()]
        headersKeyList.sort()
        q_sign_algorithm = 'sha1'
        q_ak = self.SecretId
        q_sign_time = self._get_sign_time()
        q_key_time = q_sign_time
        q_header_list = ';'.join(headersKeyList)
        q_url_param_list = ';'.join(parameterKeyList)
        HttpMethod = method.lower()
        HttpURI = '/'+filename
        q_signature = self._get_signatrue(self.SecretKey, HttpURI, HttpMethod,
                                    q_sign_algorithm, q_key_time, q_sign_time,
                                    parameters, headers)
        Authorization = {
            'q-sign-algorithm': q_sign_algorithm,
            'q-ak': q_ak,
            'q-sign-time': q_sign_time,
            'q-key-time': q_key_time,
            'q-header-list': q_header_list,
            'q-url-param-list': q_url_param_list,
            'q-signature': q_signature
        }
        print(Authorization)
        Authorization = '&'.join([k+'='+v for k, v in Authorization.items()])
        return Authorization

    def _get_sign_time(self):
        t1 = int(time.time())
        t2 = t1 + self.AuthoizationExpireTime
        return '{};{}'.format(t1, t2)

    def _get_signatrue(self, SecretKey, HttpURI, HttpMethod,
                      q_sign_algorithm, q_key_time, q_sign_time,
                      parameters, headers):
        HttpParameters =  urllib.parse.urlencode({k.lower(): v for k, v in parameters.items()})
        HttpHeaders = urllib.parse.urlencode({k.lower(): v for k, v in headers.items()})
        SignKey = hmac.new(SecretKey.encode(), q_key_time.encode(), hashlib.sha1).hexdigest()
        HttpString = "{HttpMethod}\n{HttpURI}\n{HttpParameters}\n{HttpHeaders}\n".format(
                    HttpMethod=HttpMethod, 
                    HttpURI=HttpURI,
                    HttpParameters=HttpParameters,
                    HttpHeaders=HttpHeaders)
        sha1HttpString = hashlib.sha1(HttpString.encode()).hexdigest()
        StringToSign = "{q_sign_algorithm}\n{q_sign_time}\n{sha1HttpString}\n".format(
                    q_sign_algorithm=q_sign_algorithm,
                    q_sign_time=q_sign_time,
                    sha1HttpString=sha1HttpString)
        Signature = hmac.new(SignKey.encode(), StringToSign.encode(), hashlib.sha1).hexdigest()
        return Signature

a = QCloudCOS()
a.test_get()
a.test_put()