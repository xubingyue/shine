# -*- coding: utf-8 -*-


class Request(object):
    """
    请求
    """

    conn = None
    raw_data = None
    box = None
    is_valid = False
    blueprint = None
    route_rule = None
    # 是否中断处理，即不调用view_func，主要用在before_request中
    interrupted = False

    def __init__(self, conn, raw_data):
        self.conn = conn
        self.raw_data = raw_data

    @property
    def app(self):
        return self.conn.app

    @property
    def address(self):
        return self.conn.address

    def write(self, data):
        return self.conn.write(data)

    def close(self, exc_info=False):
        self.conn.close(exc_info)

    def interrupt(self, data=None):
        """
        中断处理
        :param data: 要响应的数据，不传即不响应
        :return:
        """
        self.interrupted = True
        if data is not None:
            return self.write(data)
        else:
            return True

    def __repr__(self):
        return 'client_address: %r, raw_data: %r' % (
            self.address, self.raw_data
        )
