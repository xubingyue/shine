# -*- coding: utf-8 -*-

import zmq

connect_to = 'tcp://127.0.0.1:5001'

ctx = zmq.Context()
s = ctx.socket(zmq.SUB)
s.connect(connect_to)
s.setsockopt(zmq.SUBSCRIBE, '12')

while True:
    print s.recv_multipart()
