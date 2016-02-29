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
    def before_request(self, f):
        """
        请求解析为json成功后
        f(request)
        """

    @_reg_event_handler
    def handle_request(self, f):
        """
        处理request
        f(request)
        """

    @_reg_event_handler
    def after_request(self, f):
        """
        执行完route对应的view_func后
        f(request, exc)
        """

    @_reg_event_handler
    def before_response(self, f):
        """
        在 stream.write 之前，传入encode之后的data
        f(conn, response)
        """

    @_reg_event_handler
    def after_response(self, f):
        """
        在 stream.write 之后，传入encode之后的data
        f(conn, response, result)
        """

    @_reg_event_handler
    def close_conn(self, f):
        """
        连接close之后
        f(conn)
        """
