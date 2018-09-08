from requests import Session
from datetime import datetime
#from app.models import Article

class WeiboStatus:
    
    def __init(self, timestamp, detail):
        self.timestamp
    
    @staticmethod
    def fromJson(json):
        import json as J
        print(J.dumps(json, indent=4, ensure_ascii=False))


class Weibo:

    def __init__(self, account_id, weibo_id):
        self.account_id = account_id
        self.weibo_id = weibo_id
        self.url = 'https://m.weibo.cn/profile/info?uid=' + weibo_id
        self.session = Session()

    def syncArticles(self):
        pass

    def getWeibo(self):
        res = self.session.get(self.url)
        data = res.json()['data']
        user = data['user']
        statuses = data['statuses']
        WeiboStatus.fromJson(statuses[0]) 
        print(len(statuses))
        self.saveToArticle(statuses[0])

    def saveToArticle(self, json):
        timestamp = datetime.strptime(json['created_at'],
            "%a %b %d %H:%M:%S %z %Y")
        print(timestamp)

def addWeiboSyncJob():
    from app import scheduler

