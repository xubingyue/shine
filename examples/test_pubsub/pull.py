# -*- coding: utf-8 -*-

import zmq

connect_to = 'tcp://127.0.0.1:5001'

ctx = zmq.Context()
s = ctx.socket(zmq.PULL)
s.connect(connect_to)

while True:
    data = s.recv()
    print type(data), data
