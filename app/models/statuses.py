from flask import g
from datetime import datetime
from .. import db

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
       type=USERSTATUS, title=null, group_id=null, 
    2. 团体微博
       type=GROUPSTATUS, title=null, group_id=GROUP_ID
    3. 团体帖子
       type=GROUPPOST, title=NOT NULL, group_id=GROUP_ID
    """

    # Constants
    USERSTATUS = 0
    GROUPSTATUS = 1
    GROUPPOST = 2

    # Common
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow,
        nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False)
    type = db.Column(db.Integer, default=USERSTATUS,
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

    def to_json(self):
        imageServer = 'http://asserts.fondoger.cn/'
        json = {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'text': self.text,
            'user': self.user.to_json(),
            'timestamp': self.timestamp,
            'replies': self.replies.count(),
            'likes': self.liked_users.count(),
            'liked_by_me': hasattr(g, 'user') and g.user in self.liked_users,
            'pics': [imageServer+p.url for p in self.pictures.order_by(StatusPicture.index)],
        }
        if self.type == Status.GROUPSTATUS:
            _json = {
                'group': self.group.to_json(),
                'group_user_title': self.group.get_user_title(self.user),
            }
            json.update(_json)
        if self.type == Status.GROUPPOST:
            _json = {
                'group': self.group.to_json(),
            }
            json.update(_json)
        return json


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
