# -*- coding: utf-8 -*-

import uuid

import gevent

from ..share.log import logger


class Connection(object):

    # 唯一ID
    id = None

    # 登录之后的用户ID
    uid = None

    def __init__(self, app, stream, address):
        self.id = uuid.uuid4().hex
        self.app = app
        self.stream = stream
        self.address = address

        self.app.events.create_conn(self)

    def write(self, data):
        """
        发送数据    True: 成功   else: 失败
        """
        if self.stream.closed():
            return False

        if isinstance(data, self.app.box_class):
            # 打包
            data = data.pack()
        elif isinstance(data, dict):
            data = self.app.box_class(data).pack()

        ret = self.stream.write(data)

        return ret

    def close(self, exc_info=False):
        """
        直接关闭连接
        """
        self.stream.close(exc_info)

    def closed(self):
        """
        连接是否已经关闭
        :return:
        """
        return self.stream.closed()

    def handle(self):
        """
        启动处理
        """
        # while中判断可以保证connection_close事件只触发一次
        while not self.stream.closed():
            # 防止内存泄露
            job = gevent.spawn(self._read_message)
            job.join()

    def _read_message(self):
        data = self.stream.read_with_checker(self.app.stream_checker)
        if data:
            self._on_read_complete(data)

        # 在这里加上判断，因为如果在处理函数里关闭了conn，会导致无法触发on_connction_close
        if self.stream.closed():
            self._on_connection_close()

    def _on_connection_close(self):
        # 链接被关闭的回调

        self.app.events.close_conn(self)

    def _on_read_complete(self, data):
        """
        数据获取结束
        """
        try:
            self.app.events.handle_request(self, data)
        except Exception, e:
            logger.error('view_func raise exception. data: %s, e: %s',
                         data, e, exc_info=True)

    def __repr__(self):
        return str(self.id)
