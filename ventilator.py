# -*- coding: utf-8 -*-

"""
负责接受客户端的消息
之后转发给worker
"""

import zmq


def poll():
    ctx = zmq.Context.instance()
    s = ctx.socket(zmq.PULL)

