# -*- coding: utf-8 -*-
"""
专门给异步使用的Request封装了很多函数，可以和正常的request一样使用
"""


class VirtualRequest(object):

    trigger = None

    task = None

    def __init__(self, task, trigger):
        self.task = task
        self.trigger = trigger

    def write_to_users(self, *args, **kwargs):
        return self.trigger.write_to_users(*args, **kwargs)

    def write_to_worker(self, *args, **kwargs):
        return self.trigger.write_to_worker(*args, **kwargs)

    def close_users(self, *args, **kwargs):
        return self.trigger.close_users(*args, **kwargs)

    def write_to_client(self, data):
        return self.trigger.write_to_client(self.task, data)

    def close_client(self):
        return self.trigger.close_client(self.task)

    def login_client(self, uid, userdata=None):
        return self.trigger.login_client(self.task, uid, userdata=userdata)

    def logout_client(self):
        return self.trigger.logout_client(self.task)
