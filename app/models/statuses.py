from flask import g, current_app
from datetime import datetime
from sqlalchemy import event, orm
from sqlalchemy.sql import text
from app import db, rd
from app.utils.logger import logfuncall
from app.utils import to_http_date
from .groups import Group
import _pickle as pickle
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

    # Optional
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

    @staticmethod
    def process_json(json_status):
        import app.cache as Cache
        id = json_status['id']
        user_id = json_status['user_id']
        # Add keys
        json_status['user'] = Cache.get_user_json(user_id)
        json_status['pics'] = json.loads(json_status['pics_json'])
        json_status['liked_by_me'] = Cache.is_status_liked_by(\
                id, g.user.id) if hasattr(g, 'user') else False
        if json_status['type'] == 'GROUP_STATUS' or \
                json_status['type'] == 'GROUP_POST':
            print("TODO: using Cache.get_group")
            group = Group.query.get(json_status['group_id'])
            json_status['group'] = group.to_json()
        if json_status['type'] == 'GROUP_POST':
            print("TODO: using Cache.get_group_user_title")
            t = Cache.get_group_user_title(json_status['group_id'],
                    user_id)
            json_status['group_user_title'] = t
        # Alter keys
        json_status['timestamp'] = to_http_date(
                json_status['timestamp'])
        # Remove useless keys
        json_status.pop('pics_json', None)
        json_status.pop('user_id', None)
        json_status.pop('group_id', None)
        return json_status

    @logfuncall
    def to_json(self, cache=False):
        """
        process if cache==False
        for compatibility to old code
        """
        if not cache and current_app.config['DEBUG']:
            print("Deprecated: use Cache.get_status_json()")
        image_server = current_app.config['IMAGE_SERVER']
        pictures = [ image_server + p.url for p in
                self.pictures.order_by(StatusPicture.index) ]
        json_status = {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'text': self.text,
            'timestamp': self.timestamp.timestamp(),
            'replies': self.replies.count(),
            'likes': self.liked_users.count(),
            'group_id': self.group_id,
            'user_id': self.user_id,
            'pics_json': json.dumps(pictures, ensure_ascii=False),
        }
        if not cache:
            return Status.process_json(json_status)
        return json_status

def _clear_redis_cache(instance: Status):
    import app.cache.redis_keys as Keys
    status_id = instance.id
    keys_to_remove = [
        Keys.status_json.format(status_id),
        Keys.status_liked_users.format(status_id),
    ]
    rd.delete(*keys_to_remove)

@event.listens_for(Status, "after_insert")
@event.listens_for(Status, "after_update")
@logfuncall
def status_updated(mapper, connection, target):
    import app.cache.redis_keys as Keys
    import app.cache as Cache
    _clear_redis_cache(target)
    timeline_item = Keys.status_updated.format(
            status_id=target.id,
            user_id=target.user_id)
    rd.lpush(Keys.timeline_events_queue, timeline_item)
    # TODO: Using Cache.cache_status_json() to reduce a sql query

@event.listens_for(Status, "after_delete")
@logfuncall
def status_deleted(mapper, connection, target):
    import app.cache.redis_keys as Keys
    _clear_redis_cache(target)
    # add item to timeline queue
    timeline_item = Keys.status_deleted.format(
            status_id=target.id,
            user_id=target.user_id)
    rd.lpush(Keys.timeline_events_queue, timeline_item)

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
