# -*- coding: utf-8 -*-


from gevent.server import StreamServer
from netkit.stream import Stream

from mixins import AppEventsMixin
from connection import Connection


class Server(AppEventsMixin):
    server_class = StreamServer
    connection_class = Connection
    stream_class = Stream

    box_class = None

    # 连接最长不活跃时间
    conn_timeout = None

    backlog = None
    server = None

    def __init__(self, box_class, backlog, conn_timeout=None):
        AppEventsMixin.__init__(self)
        self.box_class = box_class
        self.backlog = backlog
        self.conn_timeout = conn_timeout

    def _handle_stream(self, sock, address):
        self.connection_class(
            self, self.stream_class(sock, use_gevent=True), address
        ).handle()

    def _prepare_server(self, address):
        import socket
        # 只有这样，才能保证在主进程里面，不会启动accept
        listener = self.server_class.get_listener(address, backlog=self.backlog, family=socket.AF_INET)
        self.server = self.server_class(listener, handle=self._handle_stream)

    def _serve_forever(self):
        self.server.serve_forever()

