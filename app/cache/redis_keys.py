"""
Ugly solution but simple.
"""


"""
User
"""

user_token = "utoken:{}"
user_token_expire = 3600*24*7

user = "user:{}"
user_expire = 3600*24*7

# TODO: change this to Redis Hash data type
user_json = "user:{}:json"
user_json_expire = 3600*24*7

# Redis set of user ids
user_followers = "user:{}:followers"
user_followers_expire = 3600*24*7

# Redis list of statuse's ids
#user_statuses = "user:{}:statuses"
#user_statuses_expire = 3600*24*7

#user_followed_num = "user:{}:followed_num"
#user_followed_num_expire = 3600*24*3

#user_group_enrolled_num = "user:{}:group_enrolled_num"
#user_group_enrolled_num_expire = 3600*24*3

# Redis sorted set
"""
element: type:id
type: s(status) or a(rticle), 1 character is faster

初始score采用帖子/动态的timestamp
有n张图片，score往后推根号n个小时
有n个字数，score往后推2n分钟
点赞一次，score 往后推一个小时
回复n次，score 往后推logn个小时
更多以后添加：
特殊用户(辅导员/教师/官方账号)动态往后推1小时

* 帖子发布、被点赞、被评论、被删除都将相应任务加入处理队列
* 用户长期未登录，timeline过期，不再更新
* 长期未登录的用户第一次访问时，先从数据库中按时间序读取若干条
* 使用zremrangebyrank, 截断取前100项
* timeline列表读取完毕后，在客户端显示没有更多内容，提示没有新微博，让用户去看热门
"""
user_timeline = "user:{}:timeline"
user_timeline_expire = 3600*24*10

# this is for elements in user_timeline, not redis key
timeline_status_item = "s:{}"
timeline_status_prefix = "s"
timeline_article_item = "a:{}"
timeline_article_prefix = "a"



"""
Status
"""
status = "status:{}"
status_expire = 3600*24*7

status_json = "status:{}:json"
status_json_expire = 3600*24*7

# Redis set of user ids
status_liked_users = "status:{}:liked_users"
status_liked_users_expire = 3600*24*7


"""
Group
"""
group = "group:{}"
group_expire = 3600*24*7

group_json = "group:{}"
group_json_expire = 3600*24*7

group_user_title = "group:{}:user:{}:title"
group_user_title_expire = 3600*24*7


"""
Task Queue
"""

"""
status_updated:status_id
status_deleted:status_id
"""
# Redis List
timeline_events_queue = "timeline_events"

status_updated = "status_updated:{}"
status_updated_prefix = "status_updated"
status_deleted = "status_deleted:{}"
status_deleted_prefix = "status_deleted"






