from flask import g
from datetime import datetime
from .. import db

# many to many
sale_likes = db.Table('sale_likes',
    db.Column('sale_id', db.Integer, db.ForeignKey('sales.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class SaleComment(db.Model):
    __tablename__ = 'sale_comments'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'),
        nullable=False) # 懒加载, 访问到属性的时候, 就会加载该属性的全部数据
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False) # joined加载, 使用join操作, 获取全部属性

    def to_json(self):
        return {
            'id': self.id,
            'text': self.text,
            'user': self.user.to_json(),
            'timestamp': self.timestamp,
        }


class SalePicture(db.Model):
    __tablename__ = 'sale_pictures'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'),
        nullable=False)
    index = db.Column(db.Integer)


class Sale(db.Model):
    __tablename__ = 'sales'

    # categorys
    CATEGORY = ['other', 'digital', 'study', 'life', 'outdoors']
    LOCATION = ['shahe', 'xueyuanlu']

    # Common
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), nullable=False)
    text = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float)
    location = db.Column(db.String(16))
    category = db.Column(db.String(16))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow,
        nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
        nullable=False)


    """ Relationships """
    pictures = db.relationship('SalePicture', backref='sale',
        lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('SaleComment', backref='sale',
        lazy='dynamic', cascade='all, delete-orphan')

    liked_users = db.relationship('User', secondary=sale_likes, lazy='dynamic', 
        backref=db.backref('liked_sales', lazy='dynamic'))

    def to_json(self):
        imageServer = 'http://asserts.fondoger.cn/'
        json = {
            'id': self.id,
            'title': self.title,
            'text': self.text,
            'price': self.price,
            'user': self.user.to_json(),
            'timestamp': self.timestamp,
            'updated_at': self.updated_at,
            'location': self.location,
            'likes': self.liked_users.count(),
            'liked_by_me': hasattr(g, 'user') and g.user in self.liked_users,
            'pics': [imageServer+p.url for p in self.pictures.order_by(SalePicture.index)],
            'comments': [c.to_json() for c in self.comments]
        }
        return json
