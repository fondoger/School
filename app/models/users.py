from flask_login import AnonymousUserMixin, UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, g
from random import randint
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app import db, rd
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql import text
from sqlalchemy import event
from time import time
import _pickle as pickle
from app.utils.logger import logfuncall
from . import redis_keys as Keys

user_follows = db.Table('user_follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

def defaultUsername(context):
    return '用户_' + str(int(time()*10000000%10000000000000000))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, nullable=False, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    # Todo: 不能为空, 两端的字符不能为空格
    username = db.Column(db.String(32), nullable=False, unique=True,
                         index=True, default=defaultUsername)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(64), nullable=False,
        default='default_avatar.jpg')
    self_intro = db.Column(db.String(40), default='')
    # 用户的性别，值为1时是男性，值为2时是女性，值为0时是未知
    gender = db.Column(db.Integer, default=0)
    # user status
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    """ Relationships """
    # 动态
    statuses = db.relationship('Status', backref='user', lazy='dynamic',
            cascade='all, delete-orphan')
    status_replies = db.relationship('StatusReply', backref='user',
            lazy='dynamic', cascade='all, delete-orphan')
    # 用户关注
    followed = db.relationship(
        'User', secondary=user_follows,
        primaryjoin=(user_follows.c.follower_id == id),
        secondaryjoin=(user_follows.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    # 团体
    group_memberships = db.relationship("GroupMembership",
        back_populates="user", cascade='all, delete-orphan', lazy='dynamic')
    # 添加直接访问方式, 可以直接通过u.groups访问到用户所在的团体
    groups = association_proxy("group_memberships", "group")
    # 二手
    sales = db.relationship('Sale', backref='user', lazy='dynamic')
    sale_comments = db.relationship('SaleComment', backref='user',
        lazy='dynamic')
    # private messages
    messages = db.relationship('Message', backref='user', lazy='dynamic')

    def generate_auth_token(self, expiration):
        s = Serializer('auth' + current_app.config['SECRET_KEY'],
                       expires_in=expiration)
        return s.dumps({'id': self.id}).decode('ascii')

    @staticmethod
    def verify_auth_token(token):
        """ Get current User from token """
        token_key = Keys.user_token.format(token)
        data = rd.get(token_key)
        if data != None:
            return User.from_id(data.decode())
        s = Serializer('auth' + current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
            rd.set(token_key, data['id'], Keys.user_token_expire)
            return User.from_id(data['id'])
        except:
            return None

    @logfuncall
    def remove_cache():
        user_key = Keys.user.format(id)
        follower_num_key = Keys.user_follower_num.format(id)
        followed_num_key = Keys.user_followed_num.format(id)
        rd.set(user_key, pickle.dumps(user), Keys.user_expire)
        rd.set(follower_num_key, self.followers.count(),
                Keys.user_follower_num_expire)
        rd.set(followed_num_key, self.followed.count(),
                Keys.user_followed_num_expire)

    @staticmethod
    @logfuncall
    def from_id(id: str):
        user_key = Keys.user.format(id)
        data = rd.get(user_key)
        if data != None:
            user = pickle.loads(data)
            user = db.session.merge(user, load=False)
            rd.expire(user_key, Keys.user_expire)
            return user
        user = User.query.get(id)
        if user:
            data = pickle.dumps(user)
            rd.set(user_key, data, Keys.user_expire)
        return user

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @logfuncall
    def _cache_followers(self):
        sql = "select follower_id from user_follows where followed_id=:UID"
        result = db.engine.execute(text(sql), UID=self.id)
        follower_ids = [ row[0] for row in result]
        follower_ids.append(-1)
        key = Keys.user_followers.format(self.id)
        """
        As redis does not support empty set, so we can't decide
        whether a empty list is cached.
        So we need a placeholder element.
        """
        rd.sadd(key, *follower_ids)
        rd.expire(key, Keys.user_followers_expire)

    @logfuncall
    def get_follower_num(self):
        key = Keys.user_followers.format(self.id)
        if not rd.exists(key):
            self._cache_followers()
        rd.expire(key, Keys.user_followers_expire)
        return rd.scard(key) - 1 # remove placeholder element

    @logfuncall
    def get_followed_num(self):
        key = Keys.user_followed_num.format(self.id)
        data = rd.get(key)
        if data != None:
            rd.expire(key, Keys.user_followed_num_expire)
            return data.decode()
        followed = self.followed.count()
        rd.set(key, followed, Keys.user_followed_num_expire)
        return followed

    @logfuncall
    def get_group_enrolled_num(self):
        key = Keys.user_group_enrolled_num.format(self.id)
        data = rd.get(key)
        if data != None:
            rd.expire(key, Keys.user_group_enrolled_num_expire)
            return data.decode()
        group_enrolled = self.group_memberships.count()
        rd.set(key, group_enrolled, Keys.user_group_enrolled_num_expire)
        return group_enrolled

    @logfuncall
    def is_followed_by(self, user_id):
        key = Keys.user_followers.format(self.id)
        if not rd.exists(key):
            self._cache_followers()
        rd.expire(key, Keys.user_followers_expire)
        return rd.sismember(key, user_id)

    @logfuncall
    def to_json(self):
        imageServer = 'http://asserts.fondoger.cn/'
        json_user = {
            'id': self.id,
            'username': self.username,
            'avatar': imageServer+self.avatar,
            'self_intro': self.self_intro,
            'gender': self.gender,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'groups_enrolled': self.get_group_enrolled_num(),
            'followed_by_me': self.is_followed_by(g.user.id),
            'followed': self.get_followed_num(),
            'followers': self.get_follower_num(),
        }
        return json_user

    def __repr__(self):
        return '<User: %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)


@event.listens_for(User, "after_update")
@event.listens_for(User, "after_delete")
def clear_cache(mapper, connection, target):
    # TODO: We don't need to drop all cache when a single column changed
    id = target.id
    keys_to_remove = []
    keys_to_remove.append(Keys.user.format(id))
    keys_to_remove.append(Keys.user_token.format(id))
    keys_to_remove.append(Keys.user_followers.format(id))
    keys_to_remove.append(Keys.user_followed_num.format(id))
    keys_to_remove.append(Keys.user_group_enrolled_num.format(id))
    rd.delete(*keys_to_remove)

def randomVerificationCode(context):
    return str(randint(100000, 999999))

class WaitingUser(db.Model):
    __classname = 'waiting_users'

    email = db.Column(db.String(64), primary_key=True)
    password_hash = db.Column(db.String(128))

    verification_time = db.Column(db.DateTime, default=datetime.utcnow)
    verification_code = db.Column(db.String(6), default=randomVerificationCode)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    @staticmethod
    def verify(email, code):
        wu = WaitingUser.query.get(email)
        if wu is None:
            return None
        if wu.verification_code != code:
            return None
        now = datetime.utcnow()
        diff = now - wu.verification_time
        minutes = divmod(diff.days * 86400 + diff.seconds, 60)[0]
        if minutes >= 15:
            return None
        return wu


