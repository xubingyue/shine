# -*- coding: utf-8 -*-

from ..share.shine_pb2 import Task, RspToUsers, CloseUsers
from ..share import constants


class Trigger(object):

    box_class = None
    forwarder_input_address_list = None

    zmq_client = None

    def __init__(self, box_class, forwarder_input_address_list, use_gevent=False):

        if use_gevent:
            import zmq.green as zmq  # for gevent
        else:
            import zmq

        self.box_class = box_class
        self.forwarder_input_address_list = forwarder_input_address_list

        ctx = zmq.Context()
        self.zmq_client = ctx.socket(zmq.PUSH)
        for address in forwarder_input_address_list:
            self.zmq_client.connect(address)

    def write_to_users(self, data_list):
        """
        格式为
        [(uids, box), (uids, box, userdata) ...]
        :param data_list: userdata可不传，默认为0，conn.userdata & userdata == userdata
        :return:
        """

        msg = RspToUsers()

        for data_tuple in data_list:
            if len(data_tuple) == 2:
                uids, data = data_tuple
                userdata = None
            else:
                uids, data, userdata = data_tuple

            if isinstance(data, self.box_class):
                data = data.pack()
            elif isinstance(data, dict):
                data = self.box_class(data).pack()

            row = msg.rows.add()
            row.buf = data
            row.userdata = userdata or 0
            row.uids.extend(uids)

        task = Task()
        task.cmd = constants.CMD_WRITE_TO_USERS
        task.data = msg.SerializeToString()

        return self.zmq_client.send(task.SerializeToString())

    def close_users(self, uids, userdata=None):
        msg = CloseUsers()
        msg.uids.extend(uids)
        msg.userdata = userdata or 0

        task = Task()
        task.cmd = constants.CMD_CLOSE_USERS
        task.data = msg.SerializeToString()

        return self.zmq_client.send(task.SerializeToString())

    def write_to_worker(self, data):
        """
        透传到worker进行处理
        """

        task = Task()
        task.client_id = self.task.client_id
        task.proc_id = self.task.proc_id
        task.cmd = constants.CMD_WRITE_TO_WORKER

        if isinstance(data, self.box_class):
            # 打包
            data = data.pack()
        elif isinstance(data, dict):
            data = self.box_class(data).pack()

        task.data = data

        return self.zmq_client.send(task.SerializeToString())
