from flask import g, current_app
from datetime import datetime
from sqlalchemy import event, orm
from sqlalchemy.sql import text
from app import db, rd
from app.utils.logger import logfuncall
import _pickle as pickle
from . import redis_keys as Keys, popularity_score as Score
import json

# many to many
status_likes = db.Table('status_likes',
    db.Column('status_id', db.Integer, db.ForeignKey('statuses.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)
# many to many
status_reply_likes = db.Table('status_reply_likes',
    db.Column('status_reply_id', db.Integer, db.ForeignKey('status_replies.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class StatusReply(db.Model):
    __tablename__ = 'status_replies'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'),
        nullable=False) # 懒加载, 访问到属性的时候, 就会加载该属性的全部数据
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False) # joined加载, 使用join操作, 获取全部属性

    # Relationships
    liked_users = db.relationship('User', secondary=status_reply_likes, lazy='dynamic')

    def to_json(self):
        return {
            'id': self.id,
            'text': self.text,
            'user': self.user.to_json(),
            'likes': self.liked_users.count(),
            'liked_by_me': g.user in self.liked_users,
            'timestamp': self.timestamp,
        }


class StatusPicture(db.Model):
    __tablename__ = 'status_pictures'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'),
        nullable=False)
    index = db.Column(db.Integer)


class Status(db.Model):
    __tablename__ = 'statuses'
    """
    可以分为三种类型的Status, 自行确保插入数据符合以下三类
    1. 普通用户动态
       type=USERS_TATUS, title=null, group_id=null,
    2. 团体微博
       type=GROUP_STATUS, title=null, group_id=GROUP_ID
    3. 团体帖子
       type=GROUP_POST, title=NOT NULL, group_id=GROUP_ID
    """
    # status type constants
    TYPES = {
        "USER_STATUS": 0,
        "GROUP_STATUS": 1,
        "GROUP_POST": 2,
    }

    # Common
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow,
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False)
    type_id = db.Column(db.Integer, default=TYPES['USER_STATUS'],
        nullable=False)

    # Specific
    title = db.Column(db.String(32))
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))

    """ Relationships """
    pictures = db.relationship('StatusPicture', backref='status',
        lazy='dynamic', cascade='all, delete-orphan')
    replies = db.relationship('StatusReply', backref='status',
        lazy='dynamic', cascade='all, delete-orphan')

    # Status => User : Status.liked_users,
    # User => Status : User.liked_status
    liked_users = db.relationship('User', secondary=status_likes, lazy='dynamic',
        backref=db.backref('liked_status', lazy='dynamic'))

    @property
    def score(self):
        # lazy load
        if not hasattr(self, '__score'):
            self.__score = Score.status(self)
        return self.__score

    @score.setter
    def score(self, new_score):
        self.__score = new_score

    @staticmethod
    @logfuncall
    def from_id(id: str):
        key = Keys.status.format(id)
        data = rd.get(key)
        if data != None:
            status = pickle.loads(data)
            status = db.session.merge(status, load=False)
            rd.expire(status, Keys.status_expire)
            return status
        status = Status.query.get(id)
        if status:
            data = pickle.dumps(status)
            rd.set(key, data, Keys.status_expire)
        return status

    @staticmethod
    @logfuncall
    def from_ids(ids):
        """
        result may not have same length of ids and
        may not returned in original order
        """
        statuses = []
        missed_ids = []
        # get from redis cache
        for index, id in enumerate(ids):
            key = Keys.status.format(id)
            data = rd.get(key)
            if data != None:
                status = pickle.loads(data)
                status = db.session.merge(status, load=False)
                statuses.append(status)
            else:
                missed_ids.append(id)
        # get from mysql
        missed = Status.query.filter(Status.id.in_(missed_ids)).all()
        for s in missed:
            statuses.append(s)
            key = Keys.status.format(id)
            data = pickle.dumps(status)
            rd.set(key, data, Keys.status_expire)
        return statuses

    @property
    def type(self):
        for k, v in Status.TYPES.items():
            if v == self.type_id:
                return k

    @type.setter
    def type(self, type_name):
        idx = Status.TYPES.get(type_name, -1)
        if idx == -1:
            raise Exception("No such type")
        self.type_id = idx

    @logfuncall
    def _cache_liked_users(self):
        sql = "select user_id from status_likes where status_id=:SID"
        result = db.engine.execute(text(sql), SID=self.id)
        liked_user_ids = [ row[0] for row in result ]
        liked_user_ids.append(-1)
        key = Keys.status_liked_users.format(self.id)
        rd.sadd(key, *liked_user_ids)
        rd.expire(key, Keys.status_liked_users_expire)

    @logfuncall
    def is_liked_by(self, user_id):
        key = Keys.status_liked_users.format(self.id)
        if not rd.exists(key):
            self._cache_liked_users()
        rd.expire(key, Keys.status_liked_users_expire)
        return rd.sismember(key, user_id)

    def to_json(self):
        key = Keys.status_json.format(self.id)
        data = rd.get(key)
        if data != None:
            rd.expire(key, Keys.status_json_expire)
            json_status = json.loads(data)
            json_status['liked_by_me'] = self.is_liked_by(g.user.id) \
                    if not g.user.is_anonymous else False
            return json_status
        image_server = current_app.config['IMAGE_SERVER']
        json_status = {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'text': self.text,
            'user': self.user.to_json(),
            'timestamp': self.timestamp,
            'replies': self.replies.count(),
            'likes': self.liked_users.count(),
            'liked_by_me': g.user in self.liked_users,
            'pics': [image_server+p.url for p in self.pictures.order_by(StatusPicture.index)],
        }
        if self.type == "GROUP_POST":
            _json_status = { 'group': self.group.to_json() }
            json_status.update(_json_status)
        if self.type == "GROUP_STATUS":
            _json_status = {
                'group': self.group.to_json(),
                'group_user_title': self.group.get_user_title(self.user),
            }
            json_status.update(_json_status)
        data = json.dumps(json_status, ensure_ascii=False)
        rd.set(key, data, ex=Keys.status_json_expire)
        return json_status


@logfuncall
@event.listens_for(Status, "after_update")
@event.listens_for(Status, "after_delete")
def clear_cache(mapper, connection, target):
    id = target.id
    keys_to_remove = []
    keys_to_remove.append(Keys.status.format(id))
    keys_to_remove.append(Keys.status_json.format(id))
    keys_to_remove.append(Keys.status_liked_users.format(id))
    rd.delete(*keys_to_remove)


# many to many
status_topic = db.Table('status_topic',
    db.Column('status_id', db.Integer, db.ForeignKey('statuses.id'), primary_key=True),
    db.Column('topic_id', db.Integer, db.ForeignKey('topics.id'), primary_key=True)
)

# many to one
class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(32), nullable=False, unique=True, index=True)

    """ Relationships """
    statuses = db.relationship('Status', secondary=status_topic, lazy='dynamic')

    def to_json(self):
        return {
            'name': self.topic,
            "statuses": self.statuses.count(),
            "followers": 0,
            "views": 0,
            'themeColor': '#c6c5ac',
        }
