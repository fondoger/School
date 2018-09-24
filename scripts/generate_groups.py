from . import *

def generate_private_groups():
    print("generating private groups...")
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
    print("success")


def generate_public_groups():
    print("generating public groups...")
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
    print("success")
