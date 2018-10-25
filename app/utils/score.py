from . import *
from datetime import datetime
import math

"""
This file provides functions to calculate scores
for statuses、articles and posts in order to
provide timeline and hot rank
"""

utc_format = '%Y-%m-%d %H:%M:%S.%f'

def timestamp_to_score(timestamp: str):
    if isinstance(timestamp, datetime):
        t = timestamp
    elif isinstance(timestamp, str):
        t = datetime.strptime(timestamp, utc_format)
    else:
        raise Exception("Wrong type")
    return int(t.timestamp())

def status(instance):
    """
    * 初始score为用户的posix timestamp
    * 有n张图片，score往后推根号n 个半小时
    * 有n个字数，score往后推2n分钟
      10个字20分钟，60个字1小时，120个字两小时
    * 有n个赞，score往后推根号n个小时
      1个赞1小时，4个赞2小时, 100个赞, 10小时
    * 有n个回复，score往后推根号n个小时

    ## 为了防止第二天上午看不到昨天的内容，
    ## 在凌晨5点统一将昨天的score加上8小时(睡眠时间)
    ## 这样就能保证昨天晚上的热门内容早上能够持续
    """
    base_score = int(instance.timestamp.timestamp())
    strlen_score = 2 * len(instance.text) * 60
    # requires a sql query
    # TODO: read from redis first
    images = instance.pictures.count()
    images_score = math.sqrt(images) * 3600 / 2
    # TODO: read from redis first
    likes = instance.liked_users.count()
    likes_score = math.sqrt(likes) * 3600
    # TODO: read from redis first
    replies = instance.replies.count()
    replies_score = math.sqrt(replies) * 3600
    score = base_score + strlen_score + images_score + likes_score + replies_score
    return score


def article(instance):
    """
    * article
    """
    base_score = int(instance.timestamp.timestamp())
    return base_score




