# -*- coding: utf-8 -*-


class Task(object):
    """
    任务，直接序列化就行
    """

    client_id = None
    proc_id = None
    cmd = None
    data = None
    topic = None

    def __init__(self, client_id, proc_id, cmd, data=None):
        """
        :param cmd:
        :param data:
        :return:
        """

        self.client_id = None
        self.proc_id = None
        self.cmd = cmd
        self.data = data
