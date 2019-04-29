"""
Ugly solution but simple.
"""

"""
User
"""

user_token = "utoken:{}"
user_token_expire = 3600 * 24 * 7

user = "user:{}"
user_expire = 3600 * 24 * 7

# TODO: change this to Redis Hash data type
# Fiels: id, username, avatar, self_intro, gender, self_intro,
# member_since, last_seen, groups_enrolled, followed, followers
user_json = "user:{}:json"
user_json_expire = 3600 * 24 * 7

# Redis set of user ids
user_followers = "user:{}:followers"
user_followers_expire = 3600 * 24 * 7

# Redis list of status's ids
# user_statuses = "user:{}:statuses"
# user_statuses_expire = 3600*24*7

# user_followed_num = "user:{}:followed_num"
# user_followed_num_expire = 3600*24*3

# user_group_enrolled_num = "user:{}:group_enrolled_num"
# user_group_enrolled_num_expire = 3600*24*3

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
# Redis sorted set
user_timeline = "user:{}:timeline"
user_timeline_expire = 3600 * 24 * 10

# this is for elements in user_timeline, not redis key
timeline_status_item = "s:{}"
timeline_status_prefix = "s"
timeline_article_item = "a:{}"
timeline_article_prefix = "a"

"""
Public timeline(Hot statuses)
"""
public_timeline = "public:timeline"

"""
Status
"""
status_json = "status:{}:json"
status_json_expire = 3600 * 24 * 7

# Redis set of user ids
status_liked_users = "status:{}:liked_users"
status_liked_users_expire = 3600 * 24 * 7

"""
Topic
"""
topic_id = "{topic_name}:id"
topic_id_expire = 3600 * 24 * 30

"""
Group
"""

# Redis String
group_json = "group:{}:json"
group_json_expire = 3600 * 24 * 7
# Redis String
group_user_title = "group:{group_id}:user:{user_id}:title"
group_user_title_expire = 3600 * 24 * 7

"""
Official Account
"""
# Redis String
official_account_json = "official_account:{}:json"
official_account_json_expire = 3600 * 24 * 7
# Redis Set
official_account_subscribers = "official_account:{}:subscribers"
official_account_subscribers_expire = 3600 * 24 * 7

"""
Articles
"""
# Redis String
article_json = "article:{}:json"
article_json_expire = 3600 * 24 * 7

"""
Task Queue
"""

# Redis List
timeline_events_queue = "timeline_events"

status_updated = "status_updated:{status_id}:{user_id}"
status_updated_prefix = "status_updated"
status_deleted = "status_deleted:{status_id}:{user_id}"
status_deleted_prefix = "status_deleted"
article_updated = "article_updated:{article_id}:{account_id}"
article_updated_prefix = "article_updated"
article_deleted = "article_deleted:{article_id}:{account_id}"
article_deleted_prefix = "article_deleted"
# A long time no-logged-in user comes back
# Insert this to right of the queue for priority
user_returned = "user_returned:{}"
user_returned_prefix = "user_returned"
