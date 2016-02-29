# -*- coding: utf-8 -*-


class Task(object):
    """
    任务，直接序列化就行
    """

    cmd = None
    body = None
    topic = None

    def __init__(self, cmd, body):
        """
        :param cmd:
        :param body:
        :return:
        """

        self.cmd = cmd
        self.body = body
