# -*- coding: utf-8 -*-

from ..share.shine_pb2 import Task, RspToUsers, CloseUsers
from ..share import constants


class Trigger(object):

    box_class = None

    zmq_client = None

    def __init__(self, box_class, forwarder_input_address_list=None, zmq_client=None, use_gevent=False):

        assert not (forwarder_input_address_list is zmq_client is None)

        self.box_class = box_class

        if forwarder_input_address_list is not None:
            if use_gevent:
                import zmq.green as zmq  # for gevent
            else:
                import zmq

            ctx = zmq.Context()
            self.zmq_client = ctx.socket(zmq.PUSH)
            for address in forwarder_input_address_list:
                self.zmq_client.connect(address)
        else:
            self.zmq_client = zmq_client

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
        task.body = msg.SerializeToString()

        return self.zmq_client.send(task.SerializeToString())

    def close_users(self, uids, userdata=None):
        msg = CloseUsers()
        msg.uids.extend(uids)
        msg.userdata = userdata or 0

        task = Task()
        task.cmd = constants.CMD_CLOSE_USERS
        task.body = msg.SerializeToString()

        return self.zmq_client.send(task.SerializeToString())

    def write_to_worker(self, data, node_id=None):
        """
        透传到worker进行处理
        还是得把node_id传过来，告诉forwarder，是要哪个node_id进行处理
        如果node_id不传，那么forwarder就会随机选择一个node_id来处理
        """

        task = Task()
        if node_id is not None:
            task.node_id = node_id
        task.cmd = constants.CMD_WRITE_TO_WORKER

        if isinstance(data, self.box_class):
            # 打包
            data = data.pack()
        elif isinstance(data, dict):
            data = self.box_class(data).pack()

        task.body = data

        return self.zmq_client.send(task.SerializeToString())
