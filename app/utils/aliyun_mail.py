import time
import hmac
import urllib.parse
import base64
import hashlib
import uuid
import requests

class AliyunEmail():
    def __init__(self):
        self.AccessKeyId = "LTAIORquvNT3iyAu"
        self.AccessKeySecret = "CjHWQYfUwNGKSSrdNXQTrPL3PAUflk"
        self.url = 'http://dm.aliyuncs.com'

    def percent_encode(self, string):
        res = urllib.parse.quote(string, '')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

    def sign(self, params):
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        can_string = (urllib.parse.urlencode(sorted_params)
                      .replace('+', '%20')
                      .replace('*', '%2A')
                      .replace('%7E', '~'))
        string_to_sign = 'GET&%2F&' + self.percent_encode(can_string)
        h = hmac.new((self.AccessKeySecret + "&").encode(),
                     string_to_sign.encode(), hashlib.sha1)
        signature = base64.encodestring(h.digest()).decode().strip()
        return signature

    def send_email(self, to_address, subject="", text_body=""):
        public_params = {
            "Format": "JSON",
            "Version": "2015-11-23",
            "AccessKeyId": self.AccessKeyId,
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "SignatureVersion": "1.0",
            "SignatureNonce": str(uuid.uuid1()),
            "RegionId": "cn-hangzhou",
        }
        single_mail_params = {
            "Action": "SingleSendMail",
            "AccountName": "admin@mail.fondoger.cn",
            "ReplyToAddress": "false",
            "AddressType": 1,
            "ToAddress": to_address,
            "FromAlias": "开发团队",
            "Subject": subject,
            "TextBody": text_body,
            "ClickTrace": 0,
        }
        params = {**public_params, **single_mail_params}
        signature = self.sign(params)
        params['Signature'] = signature
        url = self.url + '/?' + urllib.parse.urlencode(params)
        try:
            response = requests.get(url, timeout=5)
            return "EnvId" in response.json()
        except Exception as e:
            print(e)
            return False
