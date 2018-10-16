import json
from requests import Session
from datetime import datetime
from sqlalchemy.sql import exists
from sqlalchemy import and_
from bs4 import BeautifulSoup
import pytz


class BUAAArt:
    """
    :var str account_id: id of OfficialAccount
    :var str weibo_id: id of Weibo
    """

    def __init__(self, accountname, page_key):
        self.base_url = "http://artgallery.buaa.edu.cn/"
        self.accountname = accountname
        self.page_key = page_key
        self.session = Session()

    def sync(self):
        from app import db
        from app.models import Article, OfficialAccount
        from . import app

        print("Syncing BUAA Art Gallery at %s..." % self.page_key)
        articles = self.get_articles()
        new_articles = None
        with app.app_context():
            account = OfficialAccount.query.filter_by(
                accountname=self.accountname).one()
            new_articles = [
                article for article in articles
                if not db.session.query(exists().where(and_(
                    Article.type_id==Article.TYPES["BUAAART"],
                    Article.extra_key==article['key'],
                ))).scalar()
            ]
            print("Found %d new in %d buaa art gallery" %
                    (len(new_articles), len(articles)))
            if len(new_articles) == 0:
                return
        detailed_articles = [ self.get_article_detail(article)
                for article in new_articles]
        with app.app_context():
            for article in detailed_articles:
                data = {
                    "pic_url": article['pic_url'],
                    "text": article['text'],
                    "title": article['title'],
                }
                extra_data = json.dumps(data, ensure_ascii=False)
                a = Article(type="BUAAART",
                        timestamp=self.parse_time(article['date']),
                        extra_key=article['key'],
                        extra_data=extra_data,
                        extra_desc=article['title'],
                        extra_url=self.base_url + article['key'],
                        official_account=account)
                db.session.add(a)
            db.session.commit()
        print("Finished sync.")

    def get_article_detail(self, article):
        """
        :param article dict: {"key": key, "title": title}
        """
        article_url = self.base_url + article['key']
        res = self.session.get(article_url, timeout=10)
        soup = BeautifulSoup(res.content, "lxml")
        main = soup.find("ul", id="ContentBodyPart1")
        img = main.find("img")
        img_url = self.base_url + img['src'] if img else None
        count = 0
        segs = []
        for p in main.find_all("p"):
            t = p.get_text().strip()
            if not t:
                continue;
            segs.append(t)
            count += 1
            if count == 5:
                break
        text = "\n".join(segs)[:140] + "..."
        res = {
            "key": article['key'],
            "title": article['title'],
            "date": article['date'],
            "text": text,
            "pic_url": img_url,
        }
        return res

    def parse_time(self, date: str):
        utctime = datetime.strptime(date + "+0800",
                "%Y-%m-%d%z")
        now = datetime.utcnow()
        timestamp = utctime.replace(hour=now.hour, minute=now.minute)
        return timestamp.astimezone(pytz.utc)

    def get_articles(self):
        page_url = self.base_url + self.page_key + ".htm"
        res = self.session.get(page_url, timeout=10)
        soup = BeautifulSoup(res.content, "lxml")
        main = soup.find("div", class_="idx_mid_left")
        articles = main.find_all("li")
        res = []
        for article in articles:
            a = article.find("a")
            url = a['href']
            title = a['title']
            date = article.find("span").string
            res.append({"key": url, "title": title, "date": date})
        return res







