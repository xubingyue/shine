# -*- coding: utf-8 -*-

"""
负责接受客户端的消息
之后转发给worker
"""

import zmq
from netkit.stream import Stream
from netkit.box import Box
import gevent
from gevent.server import StreamServer


class RequestHandler(object):

    closed = False
    box = None

    def __init__(self, sock, address):
        self.box = Box()
        self.stream = Stream(sock)
        self.address = address
        self.handle()

    def handle(self):
        while not self.closed:
            t = gevent.spawn(self.read_message)
            t.join()

    def read_message(self):
        data = self.stream.read_with_checker(self.box.check)
        if not data:
            self.closed = True
            print 'client closed'
            return
        print "message, len: %s, content: %r" % (len(data), data)
        self.stream.write(data)


server = StreamServer(('127.0.0.1', 7777), RequestHandler)
server.serve_forever()

