# -*- coding: utf-8 -*-


import sys
from multiprocessing import Process
import time
import signal
from collections import Counter
import setproctitle

import gevent
from gevent.server import StreamServer
import functools
from netkit.stream import Stream

from .connection import Connection
from .request import Request


from ..log import logger
from .. import constants


class Gateway(object):
    enable = True
    name = constants.NAME
    processes = None
    debug = False
    got_first_request = False
    blueprints = None

    server_class = StreamServer
    connection_class = Connection
    request_class = Request
    stream_class = Stream

    box_class = None
    stream_checker = None

    backlog = constants.SERVER_BACKLOG
    server = None

    def __init__(self):
        self.processes = []
        self.blueprints = list()

    def register_blueprint(self, blueprint):
        blueprint.register_to_app(self)

    def run(self, outer_address, result_address_list, debug=None, workers=None):
        """
        启动
        :param outer_address: 外部地址 ('0.0.0.0', 9999)
        :param result_address_list: 结果地址 [('127.0.0.1', 3688), ('192.168.1.9', 3689)]
        :param debug: 是否debug
        :param workers: None: 代表以单进程模式启动；数字: 代表以master-worker方式启动。
            如果为user_reloader为True，会强制赋值为None
        :return:
        """

        if debug is not None:
            self.debug = debug

        workers = 1 if workers is None else workers

        def run_wrapper():
            logger.info('Running outer address: %s, result_address_list: %s, debug: %s, workers: %s',
                        outer_address,
                        result_address_list,
                        self.debug, workers)

            self._prepare_outer_server(outer_address)
            if workers is not None:
                setproctitle.setproctitle(self._make_proc_name('master'))
                # 只能在主线程里面设置signals
                self._handle_parent_proc_signals()
                self._fork_workers(workers)
            else:
                self._try_serve_forever(True)

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

    def _try_serve_forever(self, main_process):
        # 无论是否有master，这里都是worker
        if not main_process:
            setproctitle.setproctitle(self._make_proc_name('worker'))
            self._handle_child_proc_signals()
        else:
            setproctitle.setproctitle(self._make_proc_name('main'))

        self._before_worker_run()

        try:
            self._outer_serve_forever()
        except KeyboardInterrupt:
            pass
        except:
            logger.error('exc occur.', exc_info=True)

    def _fork_workers(self, workers):
        def start_worker_process():
            inner_p = Process(target=self._try_serve_forever, args=(False,))
            # 当前进程daemon默认是False，改成True将启动不了子进程
            # 但是子进程要设置daemon为True，这样父进程退出，子进程会被强制关闭
            # 现在父进程会在子进程之后推出，没必要设置了
            # inner_p.daemon = True
            inner_p.start()
            return inner_p

        for it in xrange(0, workers):
            p = start_worker_process()
            self.processes.append(p)

        while 1:
            for idx, p in enumerate(self.processes):
                if p and not p.is_alive():
                    self.processes[idx] = None

                    if self.enable:
                        p = start_worker_process()
                        self.processes[idx] = p

            if not filter(lambda x: x, self.processes):
                # 没活着的了
                break

            # 时间短点，退出的快一些
            time.sleep(0.1)

    def _handle_parent_proc_signals(self):
        def exit_handler(signum, frame):
            self.enable = False

            # 如果是终端直接CTRL-C，子进程自然会在父进程之后收到INT信号，不需要再写代码发送
            # 如果直接kill -INT $parent_pid，子进程不会自动收到INT
            # 所以这里可能会导致重复发送的问题，重复发送会导致一些子进程异常，所以在子进程内部有做重复处理判断。
            for p in self.processes:
                if p:
                    p.terminate()

        # INT, QUIT, TERM为强制结束
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)

    def _handle_child_proc_signals(self):
        def exit_handler(signum, frame):
            # 防止重复处理KeyboardInterrupt，导致抛出异常
            if self.enable:
                self.enable = False
                raise KeyboardInterrupt

        # 强制结束，抛出异常终止程序进行
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)

    def _handle_stream(self, sock, address):
        self.connection_class(
            self, self.stream_class(sock, use_gevent=True), address
        ).handle()

    def _prepare_outer_server(self, outer_address):
        self.server = self.server_class(outer_address, handle=self._handle_stream, backlog=self.backlog)
        self.server.start()

    def _outer_serve_forever(self):
        self.server.serve_forever()

