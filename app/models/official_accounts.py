from flask import g, current_app
from datetime import datetime
from .. import db
from .users import User
from random import randint
from sqlalchemy.ext.associationproxy import association_proxy

# many to many
article_likes = db.Table('article_likes',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
    db.Column('users_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)
# many to many
article_reply_likes = db.Table('article_reply_likes',
    db.Column('article_reply_id', db.Integer, db.ForeignKey('article_replies.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class ArticleReply(db.Model):
    __tablename__ = 'article_replies'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'),
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False)

    """ Relationships """
    liked_users = db.relationship('User', secondary=article_reply_likes, lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'text': self.text,
            'user': self.user.to_json(),
            'likes': self.liked_users.count(),
            'liked_by_me': g.user in self.liked_users,
            'timestamp': self.timestamp,
        }

class Article(db.Model):
    __tablename__ = "articles"

    """
    订阅号的文章

    站外内容：
        type: weibo/weixin
        时间：timestamp
        源地址：手动导入微信文章
        附加内容：按个网站区别对待(dumpedjson保存)

    站内内容以后再添加：
        有能力发文章的只能是非正式的团体，让他们通过团体发文章
        如果是个人的话，写文章肯定是首选公众号了。

    """
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer) # using type instead of type_id
    timestamp = db.Column(db.DateTime, default=datetime.utcnow,
            nullable=False)
    extra_url = db.Column(db.Text)
    extra_key = db.Column(db.String(32))
    extra_data = db.Column(db.Text)
    official_account_id = db.Column(db.Integer,
        db.ForeignKey('official_accounts.id'), nullable=False)

    """ Relationships """
    replies = db.relationship('ArticleReply', backref='article',
        lazy='dynamic', cascade='all, delete-orphan')
    liked_users = db.relationship('User', secondary=article_likes, lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'type': self.type,
            'text': self.text,
            'replies': self.replies.count(),
            'likes': self.liked_users.count(),
        }


    TYPES = {
        'WEIXIN': 0,
        'WEIBO': 1,
    }

    @property
    def type(self):
        for k, v in Article.TYPES:
            if v == self.type_id:
                return k
        raise Exception("no such type type_id=%d" % self.type_id)

    @type.setter
    def type(self, type_name):
        idx = Article.TYPES.get(type_name, -1)
        if idx == -1:
            raise Exception("no such type")
        self.type_id = idx


# many to many
subscriptions = db.Table('subscriptions',
    db.Column('official_account_id', db.Integer,
        db.ForeignKey('official_accounts.id'), primary_key=True),
    db.Column('users_id', db.Integer,
        db.ForeignKey('users.id'), primary_key=True),
)


class OfficialAccount(db.Model):
    __tablename__ = 'official_accounts'

    """
    类似微信订阅号功能
    首先发布爬虫爬取功能，不需要个人管理
    完善后开放个人管理
    """

    id = db.Column(db.Integer, primary_key=True)
    accountname = db.Column(db.String(32), nullable=False, index=True)
    description = db.Column(db.Text)
    avatar = db.Column(db.String(32), nullable=False)

    """ Relationships """
    articles = db.relationship('Article', backref='official_account',
        lazy='dynamic', cascade='all, delete-orphan')
    # User -> OfficialAccount: user.subscriptions
    # OfficialAccount -> User：officialAccount.subscribers
    subscribers = db.relationship('User', secondary=subscriptions,
        lazy='dynamic', backref=db.backref("subscriptions", lazy='dynamic'))

    def to_json(self):
        imageServer = current_app.config['IMAGE_SERVER']
        json = {
            'id': self.id,
            'avatar': imageServer + self.avatar,
            'accountname': self.accountname,
            'description': self.description,
            'articles': self.articles.count(),
            'subscribers': self.subscribers.count(),
        }
        return json
