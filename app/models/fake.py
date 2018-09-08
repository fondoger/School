from datetime import datetime
import forgery_py
from random import randint
from .. import db
from .users import User
from .statuses import Status, StatusReply
from .groups import Group, Activity, GroupMembership
from .official_accounts import OfficialAccount


def generate_fake_users(count=5):
    u = User(username='吃鸡小能手', email='1075004549@qq.com',
             password='y3667931', self_intro='a stupid man',
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

def generate_fake_statuses(count=100):
    user_count = User.query.count()
    print(user_count)
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        s = Status(text=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                   timestamp=forgery_py.date.date(True),
                   user=u)
        db.session.add(s)
    db.session.commit()


def generate_public_groups():
    public_groups = [
        {'category': '活在北航', 'groupname': '北航杂谈', 'avatar': 'default/group_avatar_zatan.jpg'},
        {'category': '活在北航', 'groupname': '问答互助', 'avatar': 'default/group_avatar_huzhu.jpg'},
        {'category': '活在北航', 'groupname': '聊天交友', 'avatar': 'default/group_avatar_jiaoyou.jpg'},
        {'category': '兴趣爱好', 'groupname': '影视交流'},
        {'category': '兴趣爱好', 'groupname': '音乐交流'},
        {'category': '兴趣爱好', 'groupname': '文学交流'},
        {'category': '兴趣爱好', 'groupname': '学习交流'},
        {'category': '兴趣爱好', 'groupname': '游戏交流'},
        {'category': '友校', 'groupname': '清华大学'},
        {'category': '友校', 'groupname': '北京大学'},
        {'category': '友校', 'groupname': '北京邮电大学'},
        {'category': '友校', 'groupname': '南开大学'},
        {'category': '乡音', 'groupname': '北京'},
        {'category': '乡音', 'groupname': '天津'},
        {'category': '乡音', 'groupname': '上海'},
        {'category': '乡音', 'groupname': '重庆'},
        {'category': '乡音', 'groupname': '河北'},
        {'category': '乡音', 'groupname': '山西'},
        {'category': '乡音', 'groupname': '辽宁'},
        {'category': '乡音', 'groupname': '吉林'},
        {'category': '乡音', 'groupname': '黑龙江'},
        {'category': '乡音', 'groupname': '江苏'},
        {'category': '乡音', 'groupname': '浙江'},
        {'category': '乡音', 'groupname': '安徽'},
        {'category': '乡音', 'groupname': '福建'},
        {'category': '乡音', 'groupname': '江西'},
        {'category': '乡音', 'groupname': '山东'},
        {'category': '乡音', 'groupname': '河南'},
        {'category': '乡音', 'groupname': '湖北'},
        {'category': '乡音', 'groupname': '湖南'},
        {'category': '乡音', 'groupname': '广东'},
        {'category': '乡音', 'groupname': '海南'},
        {'category': '乡音', 'groupname': '四川'},
        {'category': '乡音', 'groupname': '贵州'},
        {'category': '乡音', 'groupname': '云南'},
        {'category': '乡音', 'groupname': '陕西'},
        {'category': '乡音', 'groupname': '甘肃'},
        {'category': '乡音', 'groupname': '青海'},
        {'category': '乡音', 'groupname': '内蒙古'},
        {'category': '乡音', 'groupname': '广西'},
        {'category': '乡音', 'groupname': '西藏'},
        {'category': '乡音', 'groupname': '宁夏'},
        {'category': '乡音', 'groupname': '新疆'},
        {'category': '乡音', 'groupname': '港澳台'},
    ]
    u = User.query.first()
    for item in public_groups:
        g = Group(groupname=item['groupname'],
                  public=True,
                  category=item['category'])
        db.session.add(g)
        m = GroupMembership(group=g, user=u, title='管理员',
                            role=GroupMembership.OWNER)
        db.session.add(m)
    db.session.commit()


def generate_fake_groups():
    user = User.query.first()
    for i in ['开发团队', '测试团队', '运营团队', '推广团队', '设计团队', '产品团队']:
        g = Group(groupname=i)
        db.session.add(g)
        m = GroupMembership(group=g, user=user,
            role=GroupMembership.OWNER)
        db.session.add(m)
        for u in User.query[1:-2]:
            m = GroupMembership(group=g, user=u)
            db.session.add(m)

    db.session.commit()

def generate_fake_activities():
    activities = [
        {
            'title': '共庆2018狗年春节',
            'description': '祝大家狗年快乐',
            'group': Group.query.offset(1).first(),
            'keyword': '春节',
            'picture': 'activity_2018_spring_festival.jpg',
        },
        {
            'title': '庆祝北京航空航天大学成立56周年',
            'description': '让我们给母校过一个生日吧',
            'group': Group.query.offset(1).first(),
            'keyword': '北航生日',
            'picture': 'activity_buaa_birthday.jpg',
        },
        {
            'title': '热烈庆祝中共十九大的胜利召开',
            'description': '决胜全面建成小康社会 夺取新时代中国特色社会主义伟大胜利',
            'group': Group.query.offset(2).first(),
            'keyword': '十九大',
            'picture': 'activity_tg_19th.jpg',
        }
    ]
    for activity in activities:
        a = Activity(title=activity['title'], description=activity['description'],
                     group=activity['group'], keyword=activity['keyword'],
                     picture=activity['picture'])
        db.session.add(a)

    db.session.commit()


def generate_official_accounts():
    accounts = [
        ("北京航空航天大学", "default/official_acocunt_BUAA.jpg"),
    ]
    for name, avatar in accounts:
        a = OfficialAccount(accountname=name, avatar=avatar)
        db.session.add(a)
    db.session.commit()


def generate_fake():
    db.drop_all()
    db.create_all()


    generate_fake_users()
    generate_fake_groups()
    generate_public_groups()
    generate_fake_statuses()
    generate_fake_activities()
    generate_official_accounts()

db.generate_fake = generate_fake




