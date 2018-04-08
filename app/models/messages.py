from flask import g, current_app
from datetime import datetime
from .. import db
from . import User


class TextMessage(db.Model):
    __tablename__ = 'text_messages'
    """

    """
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    ufrom_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False)
    uto_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow,
        nullable=False)

    messages = db.relationship('Message', backref=db.backref('text_message',
        lazy=True), cascade='all, delete-orphan')

    def __repr__(self):
        return '<%r to %r: %r>' % (self.ufrom_id, self.uto_id, self.text)


class Message(db.Model):
    __tablename__ = 'messages'

    """
    设置sender_id和receiver_id是为了便于删除操作.
    在查询用户的消息时, 根据sender和receiver查询.
    当sender删除该消息时, 将sender_id设置为null.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False)
    with_id = db.Column(db.Integer)
    text_message_id = db.Column(db.Integer, db.ForeignKey('text_messages.id'))
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<user %r - %r >" % (self.user, self.text_message)

    def to_json(self, with_user=False):
        image_server = current_app.config['IMAGE_SERVER']
        u = User.query.get(self.with_id) if with_user else None
        return {
            'id': self.id,
            'ufrom_id': self.text_message.ufrom_id,
            'uto_id': self.text_message.uto_id,
            'text': self.text_message.text,
            'is_read': self.is_read,
            'timestamp': self.text_message.timestamp,
            'with': u.to_json() if u is not None else None,
        }