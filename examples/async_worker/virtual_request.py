# -*- coding: utf-8 -*-
"""
专门给异步使用的Request封装了很多函数，可以和正常的request一样使用
"""

from netkit.box import Box
from shine.share.shine_pb2 import Task
from shine.share import constants


class VirtualRequest(object):

    box_class = None
    trigger = None

    task = None
    box = None

    def __init__(self, task, box_class=None, trigger=None):
        self.task = task
        self.box_class = box_class or Box
        self.trigger = trigger

        box = self.box_class()
        box.unpack(task.body)
        self.box = box

    def write_to_users(self, *args, **kwargs):
        return self.trigger.write_to_users(*args, **kwargs)

    def write_to_worker(self, *args, **kwargs):
        return self.trigger.write_to_worker(*args, **kwargs)

    def close_users(self, *args, **kwargs):
        return self.trigger.close_users(*args, **kwargs)

    def write_to_client(self, data):
        """
        写回
        :param data: 可以是dict也可以是box
        :return:
        """

        if isinstance(data, self.box_class):
            data = data.pack()
        elif isinstance(data, dict):
            data = self.box.map(data).pack()

        task = Task()
        # 就可以直接通过node_id和client_id来进行识别了
        task.client_id = self.task.client_id
        task.node_id = self.task.node_id
        task.cmd = constants.CMD_WRITE_TO_CLIENT
        # 因为要签名，所以特殊处理
        task.body = data

        self.trigger.zmq_client.send(task.SerializeToString())
        return True

    def close_client(self):
        task = Task()
        task.client_id = self.task.client_id
        task.node_id = self.task.node_id
        task.cmd = constants.CMD_CLOSE_CLIENT

        self.trigger.zmq_client.send(task.SerializeToString())

        return True

    def login_client(self, uid, userdata=None):

        task = Task()
        task.client_id = self.task.client_id
        task.node_id = self.task.node_id
        task.cmd = constants.CMD_LOGIN_CLIENT
        task.uid = uid
        task.userdata = userdata or 0

        self.trigger.zmq_client.send(task.SerializeToString())

        return True

    def logout_client(self):
        task = Task()
        task.client_id = self.task.client_id
        task.node_id = self.task.node_id
        task.cmd = constants.CMD_LOGOUT_CLIENT

        self.trigger.zmq_client.send(task.SerializeToString())

        return True
