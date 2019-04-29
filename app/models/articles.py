from flask import g
from datetime import datetime
from app import db, rd
from sqlalchemy import event
from app.utils.logger import logfuncall
from app.utils import to_http_date

# many to many
# Typo: `users_id` should be `user_id`, but it's not easy to correct it
# As it won't influence my python code, so i decide to not change it
article_likes = db.Table('article_likes',
                         db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
                         db.Column('users_id', db.Integer, db.ForeignKey('users.id'), primary_key=True))
# many to many
article_reply_likes = db.Table('article_reply_likes',
                               db.Column('article_reply_id', db.Integer, db.ForeignKey('article_replies.id'),
                                         primary_key=True),
                               db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True))


class ArticleReply(db.Model):
    __tablename__ = 'article_replies'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

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
    type_id = db.Column(db.Integer)  # using type instead of type_id
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    extra_url = db.Column(db.Text)
    extra_key = db.Column(db.String(32))
    extra_desc = db.Column(db.String(64))
    extra_data = db.Column(db.Text)
    official_account_id = db.Column(db.Integer, db.ForeignKey('official_accounts.id'), nullable=False)

    """ Relationships """
    replies = db.relationship('ArticleReply', backref='article', lazy='dynamic', cascade='all, delete-orphan')
    liked_users = db.relationship('User', secondary=article_likes, lazy='dynamic')

    @staticmethod
    def process_json(article_json):
        import app.cache as Cache
        i = article_json['official_account_id']
        t = Cache.get_official_account_json(i)
        article_json['official_account'] = t
        article_json['timestamp'] = to_http_date(
            article_json['timestamp'])
        article_json.pop("official_account_id")
        return article_json

    def to_json(self, cache=False):
        article_json = {
            'id': self.id,
            'type': self.type,
            'timestamp': self.timestamp.timestamp(),
            'replies': self.replies.count(),
            'likes': self.liked_users.count(),
            'extra_key': self.extra_key,
            'extra_url': self.extra_url,
            'extra_data': self.extra_data,
            'extra_desc': self.extra_desc,
            'official_account_id': self.official_account_id,
        }
        if not cache:
            return Article.process_json(article_json)
        return article_json

    TYPES = {
        'WEIXIN': 0,
        'WEIBO': 1,
        'BUAANEWS': 2,
        'BUAAART': 3,
    }

    @property
    def type(self):
        for k, v in Article.TYPES.items():
            if v == self.type_id:
                return k
        raise Exception("no such type type_id=%d" % self.type_id)

    @type.setter
    def type(self, type_name):
        idx = Article.TYPES.get(type_name, -1)
        if idx == -1:
            raise Exception("no such type")
        self.type_id = idx


def _clear_redis_cache(instance: Article):
    import app.cache.redis_keys as Keys
    article_id = instance.id
    keys_to_remove = [
        Keys.article_json.format(article_id),
    ]
    rd.delete(*keys_to_remove)


@logfuncall
@event.listens_for(Article, "after_insert")
@event.listens_for(Article, "after_update")
def article_updated(mapper, connection, target):
    import app.cache.redis_keys as Keys
    _clear_redis_cache(target)
    # add item to timeline queue
    timeline_item = Keys.article_updated.format(
        article_id=target.id,
        account_id=target.official_account_id)
    rd.lpush(Keys.timeline_events_queue, timeline_item)
    # TODO: Using Cache.cache_article_json() to reduce a sql query


@logfuncall
@event.listens_for(Article, "after_delete")
def article_delete(mapper, connection, target):
    import app.cache.redis_keys as Keys
    _clear_redis_cache(target)
    timeline_item = Keys.article_deleted.format(
        article_id=target.id,
        account_id=target.official_account_id)
    rd.lpush(Keys.timeline_events_queue, timeline_item)
