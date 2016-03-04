# -*- coding: utf-8 -*-

"""
共享存储
用来保存进程唯一ID，用户所在位置等
"""


class ShareStore(object):

    rds = None
    user_key_prefix = None
    procs_key = None
    user_maxage = None

    def __init__(self, rds, user_key_prefix, procs_key, user_maxage=None):
        """
        :param rds: redis实例
        :param user_key_prefix: 用户数据的key前缀
        :param procs_key: 进程集合的key
        :return:
        """

        self.rds = rds
        self.user_key_prefix = user_key_prefix
        self.procs_key = procs_key
        self.user_maxage = user_maxage

    def add_user(self, uid, proc_id):
        """
        添加用户
        :param uid:
        :param proc_id:
        :return:
        """
        return self.rds.set(self._make_redis_key(uid), proc_id, ex=self.user_maxage)

    def remove_user(self, uid, proc_id):
        """
        删除用户，要保证proc_id相等
        :param uid:
        :return:
        """

        old_proc_id = self.rds.get(self._make_redis_key(uid))

        if old_proc_id is None:
            # 没数据当然直接返回啦
            return

        return self.rds.delete(self._make_redis_key(uid))

    def add_proc(self, proc_id):
        """
        添加proc_id
        :return:
        """

        return self.rds.sadd(self.procs_key, proc_id)

    def remove_proc(self, proc_id):
        """
        删除proc_id
        :return:
        """

        return self.rds.srem(self.procs_key, proc_id)

    def _make_redis_key(self, uid):
        return self.user_key_prefix + str(uid)
