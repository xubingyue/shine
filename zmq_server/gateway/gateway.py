# -*- coding: utf-8 -*-


import signal
import sys
import gevent
import setproctitle

from ..server import Server
from ..master import Master
from ..log import logger
from .. import constants


class Gateway(object):
    name = constants.NAME
    debug = False

    master = None
    outer_server = None

    outer_address = None
    inner_address = None

    result_address_list = None

    def __init__(self, box_class):
        self.master = Master()
        self.outer_server = Server(box_class)

    def run(self, outer_address, inner_address, result_address, debug=None, workers=None):
        """
        启动
        :param outer_address: 外部地址 ('0.0.0.0', 9999)
        :param inner_address: 内部地址 ('0.0.0.0', 10999)
        :param result_address: 结果地址 [('127.0.0.1', 3688), ('192.168.1.9', 3689)]
        :param debug: 是否debug
        :param workers: None: 代表以单进程模式启动；数字: 代表以master-worker方式启动。
            如果为user_reloader为True，会强制赋值为None
        :return:
        """

        self.outer_address = outer_address
        self.inner_address = inner_address
        self.result_address_list = result_address

        if debug is not None:
            self.debug = debug

        workers = 1 if workers is None else workers

        def run_wrapper():
            logger.info('Running outer address: %s, result_address: %s, debug: %s, workers: %s',
                        outer_address,
                        result_address,
                        self.debug, workers)

            self._prepare_server()
            setproctitle.setproctitle(self._make_proc_name('master'))
            # 只能在主线程里面设置signals
            self._handle_parent_proc_signals()
            self.master.fork_workers(workers, self._try_serve_forever)

        run_wrapper()

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

    def _before_worker_run(self):
        pass

    def _prepare_server(self):
        """
        准备server，因为fork之后就晚了
        :return:
        """
        self.outer_server._prepare_server(self.outer_address)

    def _serve_forever(self):
        """
        保持运行
        :return:
        """
        job_list = []
        for action in [self.outer_server._serve_forever,]:
            job_list.append(gevent.spawn(action))

        for job in job_list:
            job.join()

    def _try_serve_forever(self):
        self._handle_child_proc_signals()

        self._before_worker_run()

        try:
            self._serve_forever()
        except KeyboardInterrupt:
            pass
        except:
            logger.error('exc occur.', exc_info=True)

    def _handle_parent_proc_signals(self):
        def exit_handler(signum, frame):
            self.master.enable = False

            # 如果是终端直接CTRL-C，子进程自然会在父进程之后收到INT信号，不需要再写代码发送
            # 如果直接kill -INT $parent_pid，子进程不会自动收到INT
            # 所以这里可能会导致重复发送的问题，重复发送会导致一些子进程异常，所以在子进程内部有做重复处理判断。
            self.master.terminate_all()

        # INT, QUIT, TERM为强制结束
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)

    def _handle_child_proc_signals(self):
        def exit_handler(signum, frame):
            # 防止重复处理KeyboardInterrupt，导致抛出异常
            if self.master.enable:
                self.master.enable = False
                raise KeyboardInterrupt

        # 强制结束，抛出异常终止程序进行
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)
