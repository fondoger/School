from flask import g
from flask import current_app
from datetime import datetime
from .. import db
from .users import User
from random import randint
from sqlalchemy.ext.associationproxy import association_proxy

def defaultTitle(context):
    role = context.current_parameters.get('role')
    if role == GroupMembership.OWNER:
        return '持有者'
    elif role == GroupMembership.ADMIN:
        return '管理员'
    else:
        return '成员'

class GroupMembership(db.Model):
    __tablename__ = 'group_memberships'
    """
    Many to Many Relationship between User and Group 

    三种类型: 持有人, 管理员, 成员
    其中, 只有持有人和管理员才能自定义称号

    Note: 
    1. 移交所有权时, 自身变为普通成员
    """

    # static constants
    MEMBER = 0  # 普通成员
    ADMIN = 1   # 管理员
    OWNER = 2   # 持有者
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
                            primary_key=True)

    role = db.Column(db.Integer, nullable=False, default=MEMBER)
    title = db.Column(db.String(32), nullable=False, default=defaultTitle)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="group_memberships")  
    group = db.relationship("Group", back_populates="group_memberships")
 
    def to_json(self):
        return {
            'user': self.user.to_json(),
            'role': self.role,
            'title': self.title,
            'timestamp': self.timestamp
        }


class Group(db.Model):
    __tablename__ = 'groups'

    """
    Note:
    1. 创建Group时, 需另外建立一个User和Group的Group的GroupMembership

    * 普通团体
    1. Owner可以发起活动
    2. Owner和Admin可以以团体名义发动态
    3. 团体成员可以在团体内部发动态

    * 公开团体与普通团体的不同
    1. 公开团体发帖没有成员限制
    2. 只有一个管理员即Owner, 只能管理团体内容, 无法修改或删除团体
    3. 不能以团体名义发起活动, 不能以团体名义发动态
    """

    id = db.Column(db.Integer, primary_key=True)
    groupname = db.Column(db.String(32), nullable=False, unique=True,
                         index=True)
    description = db.Column(db.String(64))
    avatar = db.Column(db.String(32), default='default_group_avatar.jpg',
        nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    public = db.Column(db.Boolean, default=False, nullable=False)
    # 除了公开团体有自己的category, 其余所有团体都是普通团体
    category = db.Column(db.String(32), default='普通团体')

    """ Relationships """
    group_memberships = db.relationship("GroupMembership", back_populates="group",
        cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='group', lazy='dynamic',
        cascade='all, delete-orphan')
    statuses = db.relationship('Status', backref='group', lazy='dynamic')

    def __repr__(self):
        return '<Group: %r>' % self.groupname

    @property
    def members(self):
        return [ m.users for m in self.group_memberships]

    def get_owner(self):
        for m in self.group_memberships:
            if m.role == GroupMembership.OWNER:
                return m.user
        raise Exception('Group %s has no onwer' % self.groupname)

    def get_user_title(self, user):
        # todo: 该函数可以优化, 应该能直接得到关系
        # eg: group_memberships.get(group=self, user_id=user)
        for m in self.group_memberships:
            if m.user == user:
                return m.title
        return ''

    def to_json(self):
        imageServer = current_app.config['IMAGE_SERVER']
        return {
            'id': self.id,
            'description': self.description,
            'groupname': self.groupname,
            'avatar': imageServer + self.avatar,
            'public': self.public,
            'category': self.category,
            'created_at': self.created_at,
            'daily_statuses': self.statuses.count(),
        }


class Activity(db.Model):
    __tablename__ = 'activities'
    """
    1. 只有团体所有者才能发起活动
    2. 每个活动必须指明一个微博话题
    """

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(64))
    text = db.Column(db.String(256))
    keyword = db.Column(db.String(32), nullable=False, default='默认活动')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
        nullable=False)
    picture = db.Column(db.Text, default='default_activity_cover.jpg',
        nullable=False)

    def to_json(self):
        imageServer = current_app.config['IMAGE_SERVER']

        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'text': self.text,
            'timestamp': self.timestamp,
            'keyword': self.keyword,
            'group': self.group.to_json(),
            'picture': imageServer + self.picture,
        }



