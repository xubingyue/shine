# coding: utf8

import time
import zmq


def pull():
    bind_to = 'tcp://127.0.0.1:5001'
    ctx = zmq.Context()
    s = ctx.socket(zmq.PULL)
    s.bind(bind_to)

    return s


def pub():
    bind_to = 'tcp://127.0.0.1:5002'
    ctx = zmq.Context()
    s = ctx.socket(zmq.PUB)
    s.bind(bind_to)
    return s

s_pull = pull()
s_pub = pub()

print s_pull.recv()

raw_input()
