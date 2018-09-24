from . import *
from random import randint
import forgery_py

def generate_fake_statuses(count=100):
    print("generating fake statuses...")
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        s = Status(text=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                   timestamp=forgery_py.date.date(True),
                   user=u)
        db.session.add(s)
    db.session.commit()
    print("success")