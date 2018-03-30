import time
import hmac
import urllib.parse
import base64
import hashlib
import uuid
import requests

ActivationSubject = "欢迎注册，请验证您的邮箱"

ActivationText = """尊敬的用户，您好！

验证码： {code} 
(15分钟内有效)

您正在使用该邮箱注册某北航社交平台，我们需要验证这是您的邮箱，如果这不是您的操作，请忽略该邮件。

系统发信, 请勿回复
服务邮箱：service@fondoger.cn
"""

class AliyunEmail():
    def __init__(self):
        self.AccessKeyId = "LTAIORquvNT3iyAu"
        self.AccessKeySecret = "CjHWQYfUwNGKSSrdNXQTrPL3PAUflk"
        self.url = 'http://dm.aliyuncs.com'

    def percentEncode(self, str):
        res = urllib.parse.quote(str, '')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

    def sign(self, params):
        sortedParams = sorted(params.items(), key=lambda x: x[0])
        canString = (urllib.parse.urlencode(sortedParams)
                                    .replace('+', '%20')
                                    .replace('*', '%2A')
                                    .replace('%7E', '~'))
        stringToSign = 'GET&%2F&' + self.percentEncode(canString)
        h = hmac.new((self.AccessKeySecret + "&").encode(),
                     stringToSign.encode(), hashlib.sha1)
        signature = base64.encodestring(h.digest()).decode().strip()
        return signature

    def _send(self, toAddress, subject, textBody):
        PublicParams = {
            "Format": "JSON",
            "Version": "2015-11-23",
            "AccessKeyId": self.AccessKeyId,
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "SignatureVersion": "1.0",
            "SignatureNonce": str(uuid.uuid1()),
            "RegionId": "cn-hangzhou",
        }
        SingleMailParams = {
            "Action": "SingleSendMail",
            "AccountName": "admin@mail.fondoger.cn",
            "ReplyToAddress": "false",
            "AddressType": 1,
            "ToAddress": toAddress,
            "FromAlias": "开发团队",
            "Subject": subject,
            "TextBody": textBody,
            "ClickTrace": 0,
        }
        params = {**PublicParams, **SingleMailParams}
        signature = self.sign(params)
        params['Signature'] = signature
        url = self.url + '/?' + urllib.parse.urlencode(params)
        try:
            response = requests.get(url, timeout=5)
            return ("EnvId" in response.json())
        except Exception as e:
            print(e)
            return False

    def sendActivationEmail(self, email, code):
        textBody = (ActivationText.replace("{code}", str(code)))
        return self._send(email, ActivationSubject, textBody)
    
