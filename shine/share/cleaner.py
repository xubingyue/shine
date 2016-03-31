# -*- coding: utf-8 -*-

"""
负责清理过期的数据
"""

from ..share import constants
from ..share.config import Config


class Cleaner(object):

    def __init__(self):
        self.config = Config(defaults=constants.DEFAULT_CONFIG)

    def clean_redis(self):
        if not self.config['REDIS_URL']:
            # 没有配置redis的话，就直接返回就好
            return

        import redis
        rds = redis.from_url(self.config['REDIS_URL'])
        user_key_prefix = self.config['REDIS_KEY_SHARE_PREFIX'] + self.config['REDIS_USER_KEY_PREFIX']
        nodes_key = self.config['REDIS_KEY_SHARE_PREFIX'] + self.config['REDIS_NODES_KEY']

        rds.delete(nodes_key)

        for user_key in rds.keys('%s*' % user_key_prefix):
            rds.delete(user_key)
