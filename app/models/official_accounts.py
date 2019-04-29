from flask import g, current_app
from app import db, rd
from sqlalchemy import event

# many to many
# Typo: `users_id` should be `user_id`, but it's not easy to correct it
# As it won't influence my python code, so i decide to not change it
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
    accountname = db.Column(db.String(32), index=True,
                            unique=True, nullable=False)
    description = db.Column(db.Text)
    avatar = db.Column(db.String(64), nullable=False)
    page_url = db.Column(db.String(64))

    """ Relationships """
    articles = db.relationship('Article', backref='official_account',
                               lazy='dynamic', cascade='all, delete-orphan')
    # User -> OfficialAccount: user.subscriptions
    # OfficialAccount -> User：officialAccount.subscribers
    subscribers = db.relationship('User', secondary=subscriptions, lazy='dynamic',
                                  backref=db.backref("subscriptions", lazy='dynamic'))

    @staticmethod
    def process_json(json_account):
        import app.cache as Cache
        json_account['followed_by_me'] = Cache.is_account_followed_by( json_account['id'], g.user.id) \
            if hasattr(g, 'user') else False
        return json_account

    def to_json(self, cache=False):
        image_server = current_app.config['IMAGE_SERVER']
        json_account = {
            'id': self.id,
            'avatar': image_server + self.avatar,
            'accountname': self.accountname,
            'description': self.description,
            'page_url': self.page_url,
            'articles': self.articles.count(),
            'subscribers': self.subscribers.count(),
        }
        if not cache:
            return OfficialAccount.process_json(json_account)
        return json_account

    def __repr__(self):
        return '<OfficialAccount: %r>' % self.accountname


def _remove_redis_cache(instance: OfficialAccount):
    import app.cache.redis_keys as KEYS
    id = instance.id
    keys_to_remove = [
        KEYS.official_account_json.format(id),
        KEYS.official_account_subscribers.format(id),
    ]
    rd.delete(*keys_to_remove)


@event.listens_for(OfficialAccount, "after_delete")
@event.listens_for(OfficialAccount, "after_update")
def account_deleted(mapper, connection, target):
    _remove_redis_cache(target)
