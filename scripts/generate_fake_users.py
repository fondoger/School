from app import db, models
from app.models import *
import forgery_py


def generate_fake_users(count=5):
    print("generating fake users...")
    u = User(username='吃鸡小能手', email='1075004549@qq.com',
             password='y3667931', self_intro='游走在挂科的边缘',
             avatar='test_avatar.jpg')
    db.session.add(u)
    for i in range(count):
        u = User(username=forgery_py.internet.user_name(True),
                 email=forgery_py.internet.email_address(),
                 password=forgery_py.lorem_ipsum.word(),
                 self_intro=forgery_py.lorem_ipsum.sentence()[:40],
                 member_since=forgery_py.date.date(True),
                 last_seen=forgery_py.date.date(True))
        if User.query.filter_by(email=u.email).first() is None and \
                User.query.filter_by(username=u.username).first() is None:
            db.session.add(u)
    db.session.commit()
    print("success")