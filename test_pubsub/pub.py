# -*- coding: utf-8 -*-

import time
import zmq

bind_to = 'tcp://127.0.0.1:5001'

ctx = zmq.Context()
s = ctx.socket(zmq.PUB)
s.bind(bind_to)

while True:
    s.send_multipart(['123', 'body'])
    time.sleep(1)

raw_input()
