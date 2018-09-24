from . import *

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