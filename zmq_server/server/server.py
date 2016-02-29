# -*- coding: utf-8 -*-


import sys

from gevent.server import StreamServer
from netkit.stream import Stream

from .connection import Connection
from zmq_server.share import constants


class Server(object):
    enable = True
    name = constants.NAME

    server_class = StreamServer
    connection_class = Connection
    stream_class = Stream

    box_class = None
    stream_checker = None

    backlog = constants.SERVER_BACKLOG
    server = None

    def __init__(self, box_class):
        self.box_class = box_class

    def _make_proc_name(self, subtitle):
        """
        获取进程名称
        :param subtitle:
        :return:
        """
        proc_name = '[%s %s:%s] %s' % (
            self.name,
            constants.NAME,
            subtitle,
            ' '.join([sys.executable] + sys.argv)
        )

        return proc_name

    def _handle_stream(self, sock, address):
        self.connection_class(
            self, self.stream_class(sock, use_gevent=True), address
        ).handle()

    def _prepare_server(self, outer_address):
        self.server = self.server_class(outer_address, handle=self._handle_stream, backlog=self.backlog)
        self.server.start()

    def _serve_forever(self):
        self.server.serve_forever()

