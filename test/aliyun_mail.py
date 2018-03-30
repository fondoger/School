import time
import hmac
import urllib.parse
import base64
import hashlib
import uuid
import requests

ActivationSubject = "欢迎注册XXX，请验证您的邮箱"
ActivationHtml = """<p>尊敬的用户： {username}，<br>您好！</p>
<p>
您正在使用该邮箱注册XXX，我们需要验证这是您的邮箱，点击以下链接验证：<br>
<a href="http://fondoger.cn/activate?token={token}">http://fondoger.cn/activate?token={token}</a><br>
(如果链接无法点击, 请复制到浏览器打开)
</p>
<p>
系统发信, 请勿回复<br>
服务邮箱：service@fondoger.cn
</p>
<p>
如果这不是您的操作，请忽略该邮件<br>
或者<a href="http//fondoger.cn/unsubscribe?token={unsubscrib_token}">点此退订</a>(您将不再收到我们的任何邮件)
</p>
"""
ActivationText = """尊敬的用户：{username}，
您好！
您正在使用该邮箱注册掌上北航社交平台，我们需要验证这是您的邮箱，复制以下链接到浏览器打开：<br>
http://fondoger.cn/activate?token={token}

系统发信, 请勿回复
服务邮箱：service@fondoger.cn

如果这不是您的操作，请忽略该邮件
或者点此退订(您将不再收到我们的任何邮件)：
http//fondoger.cn/unsubscribe?token={unsubscrib_token}
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
        print(stringToSign)
        h = hmac.new((self.AccessKeySecret + "&").encode(),
                     stringToSign.encode(), hashlib.sha1)
        signature = base64.encodestring(h.digest()).decode().strip()
        return signature

    def send(self, toAddress, subject, htmlBody, textBody):
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
            "AddressType": 0,
            "ToAddress": toAddress,
            "FromAlias": "开发团队",
            "Subject": subject,
            "HtmlBody": htmlBody,
            "TextBody": textBody,
            "ClickTrace": 0,
        }
        params = {**PublicParams, **SingleMailParams}
        signature = self.sign(params)
        params['Signature'] = signature
        url = self.url + '/?' + urllib.parse.urlencode(params)
        try:
            response = requests.get(url)
            return ("EnvId" in response.json())
        except Exception as e:
            print(e)
            return False

    def sendActivationEmail(self, email, username, token):
        htmlBody = (ActivationHtml.replace("{username}", username)
                    .replace("{token}", token)
                    .replace("{unsubscrib_token}", str(uuid.uuid1())))
        textBody = (ActivationText.replace("{username}", username)
                    .replace("{token}", token)
                    .replace("{unsubscrib_token}", str(uuid.uuid1())))
        return self.send(email, ActivationSubject, htmlBody, textBody)
    

aliyun = AliyunEmail()
print(aliyun.sendActivationEmail("roujimail@163.com", "Fondoger", "this_is_a_token"))
