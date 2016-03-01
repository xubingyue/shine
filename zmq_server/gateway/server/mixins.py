# -*- coding: utf-8 -*-

import functools
from events import Events

from .utils import safe_func


def _reg_event_handler(func):
    @functools.wraps(func)
    def func_wrapper(obj, handler):
        event = getattr(obj.events, func.__name__)
        event += safe_func(handler)

        return handler
    return func_wrapper


class AppEventsMixin(object):
    events = None

    def __init__(self):
        self.events = Events()

    @_reg_event_handler
    def create_conn(self, f):
        """
        连接建立成功后
        f(conn)
        """

    @_reg_event_handler
    def handle_request(self, f):
        """
        处理request
        f(conn, data)
        """

    @_reg_event_handler
    def close_conn(self, f):
        """
        连接close之后
        f(conn)
        """
