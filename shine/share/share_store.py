# -*- coding: utf-8 -*-

"""
共享存储
用来保存进程唯一ID，用户所在位置等
"""


class ShareStore(object):

    rds = None
    user_key_prefix = None
    nodes_key = None
    user_maxage = None

    def __init__(self, rds, user_key_prefix, nodes_key, user_maxage=None):
        """
        :param rds: redis实例
        :param user_key_prefix: 用户数据的key前缀
        :param nodes_key: 进程集合的key
        :return:
        """

        self.rds = rds
        self.user_key_prefix = user_key_prefix
        self.nodes_key = nodes_key
        self.user_maxage = user_maxage

    def add_user(self, uid, node_id):
        """
        添加用户
        :param uid:
        :param node_id:
        :return:
        """
        return self.rds.set(self._make_redis_key(uid), node_id, ex=self.user_maxage)

    def remove_user(self, uid, node_id):
        """
        删除用户，要保证node_id相等
        :param uid:
        :return:
        """

        old_node_id = self.rds.get(self._make_redis_key(uid))

        if old_node_id is None:
            # 没数据当然直接返回啦
            return

        return self.rds.delete(self._make_redis_key(uid))

    def get_users(self, uid_list):
        """
        批量获取用户信息 {
            1: "223",
            2: "333",
        }
        :param uid_list:
        :return:
        """
        node_id_list = self.rds.mget([self._make_redis_key(uid) for uid in uid_list])

        return dict(zip(uid_list, node_id_list))

    def add_node(self, node_id):
        """
        添加node_id
        :return:
        """

        return self.rds.sadd(self.nodes_key, node_id)

    def remove_node(self, node_id):
        """
        删除node_id
        :return:
        """

        return self.rds.srem(self.nodes_key, node_id)

    def get_nodes(self):
        """
        获取proc集合
        :return:
        """
        return self.rds.smembers(self.nodes_key)

    def _make_redis_key(self, uid):
        return self.user_key_prefix + str(uid)
