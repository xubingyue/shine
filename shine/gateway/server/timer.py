# -*- coding: utf-8 -*-

import gevent
from .utils import safe_call


class Timer(object):

    timer = None

    def set(self, interval, callback, repeat=False, force=True):
        """
        添加timer
        """
        if self.timer:
            if force:
                # 如果已经存在，那么先要把现在的清空
                self.clear()
            else:
                # 已经存在的话，就返回了
                return

        def callback_wrapper():
            # 必须要确定，这次调用就是这个timer引起的
            if self.timer == timer:
                # 必须加这句，否则如果在callback中有clear操作，会出现GreenletExit
                self.timer = None
                # 不可以加 timer = None，否则会导致判断self.timer == timer 报错找不到timer
                result = safe_call(callback)
                if repeat and not self.timer:
                    # 之所以还要判断timer，是因为callback中可能设置了新的回调
                    self.set(interval, callback, repeat, True)
                return result

        self.timer = timer = gevent.spawn_later(interval, callback_wrapper)

    def clear(self):
        """
        直接把现在的清空
        """
        if not self.timer:
            return

        # 不阻塞
        try:
            self.timer.kill(block=False)
        except:
            pass
        self.timer = None
