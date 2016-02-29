# -*- coding: utf-8 -*-


import signal
import sys
import setproctitle
import zmq
from ..share.proc_mgr import ProcMgr
from ..share.log import logger
from ..share import constants, gw_pb2


class Gateway(object):
    name = constants.NAME
    debug = False

    proc_mgr = None
    zmq_pull_server = None
    zmq_pub_client = None

    pull_address_list = None
    pub_address_list = None

    def __init__(self):
        self.proc_mgr = ProcMgr()

    def run(self, pull_address_list, pub_address_list, debug=None):
        """
        启动
        :param pull_address_list: 内部地址列表 [tcp://127.0.0.1:8833, ]，worker参数不需要了，就是内部地址列表的个数
        :param pub_address_list: 结果地址列表 [tcp://127.0.0.1:8855, ]
        :param debug: 是否debug
        :return:
        """

        self.pull_address_list = pull_address_list
        self.pub_address_list = pub_address_list

        if debug is not None:
            self.debug = debug

        workers = len(self.pull_address_list)

        def run_wrapper():
            logger.info('Running pull_address_list: %s, pub_address_list: %s, debug: %s, workers: %s',
                        pull_address_list,
                        pub_address_list,
                        self.debug, workers)

            setproctitle.setproctitle(self._make_proc_name('resulter:master'))
            # 只能在主线程里面设置signals
            self._handle_parent_proc_signals()
            self.proc_mgr.fork_workers(workers, self._worker_run)

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

    def _serve_forever(self):
        """
        保持运行
        :return:
        """

        while 1:
            data = self.zmq_pull_server.recv_string()

            task = gw_pb2.Task()
            task.ParseFromString(data)

            # TODO 先只处理write_to_client的方式
            if task.cmd == constants.CMD_WRITE_TO_CLIENT:
                # 原样处理过去
                self.zmq_pub_client.send(
                    (task.proc_id, data)
                )

    def _start_pull_server(self, address):
        """
        zmq的pull server
        每个worker绑定的地址都要不一样
        """
        ctx = zmq.Context()
        self.zmq_pull_server = ctx.socket(zmq.PULL)
        self.zmq_pull_server.bind(address)

    def _start_pub_server(self, address):
        """
        zmq的pub server
        每个worker绑定的地址都要不一样
        """
        ctx = zmq.Context()
        self.zmq_pull_server = ctx.socket(zmq.PUB)
        self.zmq_pull_server.bind(address)

    def _worker_run(self, index):
        """
        在worker里面执行的
        :return:
        """
        setproctitle.setproctitle(self._make_proc_name('resulter:worker:%s' % index))
        self._handle_child_proc_signals()

        self._start_pull_server(self.pull_address_list[index])
        self._start_pub_server(self.pub_address_list[index])

        try:
            self._serve_forever()
        except KeyboardInterrupt:
            pass
        except:
            logger.error('exc occur.', exc_info=True)

    def _handle_parent_proc_signals(self):
        def exit_handler(signum, frame):
            self.proc_mgr.enable = False

            # 如果是终端直接CTRL-C，子进程自然会在父进程之后收到INT信号，不需要再写代码发送
            # 如果直接kill -INT $parent_pid，子进程不会自动收到INT
            # 所以这里可能会导致重复发送的问题，重复发送会导致一些子进程异常，所以在子进程内部有做重复处理判断。
            self.proc_mgr.terminate_all()

        # INT, QUIT, TERM为强制结束
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)

    def _handle_child_proc_signals(self):
        def exit_handler(signum, frame):
            # 防止重复处理KeyboardInterrupt，导致抛出异常
            if self.proc_mgr.enable:
                self.proc_mgr.enable = False
                raise KeyboardInterrupt

        # 强制结束，抛出异常终止程序进行
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        signal.signal(signal.SIGTERM, exit_handler)
