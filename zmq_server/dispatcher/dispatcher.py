# -*- coding: utf-8 -*-


import signal
import sys
import weakref
import uuid
import setproctitle

import gevent
from gevent.queue import Queue
import zmq.green as zmq  # for gevent

from .server import Server
from ..share.proc_mgr import ProcMgr
from ..share.log import logger
from ..share import constants, gw_pb2


class Dispatcher(object):
    name = constants.NAME
    debug = False

    proc_mgr = None
    outer_server = None
    zmq_inner_server = None
    zmq_forwarder_client = None

    # 准备发送到worker的queue
    task_queue = None

    outer_host = None
    outer_port = None
    inner_address_list = None
    forwarder_address_list = None

    # worker唯一标示
    worker_uuid = None
    # 连接ID->conn
    conn_dict = None
    # 用户ID->conn
    user_dict = None

    user_redis_url = None
    user_redis_key_tpl = None
    # 最长存储的秒数，因为有可能有些用户的数据没有正常清空
    user_redis_maxage = None
    # 存储存储userid->proc_id
    user_redis = None

    def __init__(self, box_class):
        self.proc_mgr = ProcMgr()
        self.outer_server = Server(box_class)
        self.task_queue = Queue()

    def run(self, outer_host, outer_port, inner_address_list, forwarder_address_list,
            user_redis_url=None, user_redis_key_tpl=None, user_redis_maxage=None,
            debug=None):
        """
        启动
        :param outer_host: 外部地址 '0.0.0.0'
        :param outer_port: 外部地址 7100
        :param inner_address_list: 内部地址列表 [tcp://127.0.0.1:8833, ]，worker参数不需要了，就是内部地址列表的个数
        :param forwarder_address_list: 结果地址列表 [tcp://127.0.0.1:8855, ]
        :param user_redis_url: redis存储的url，不传的话，相当于不走分布式
        :param user_redis_key_tpl: redis存储的key模板，如 'zmq:user:%s'
        :param debug: 是否debug
        :return:
        """

        self.outer_host = outer_host
        self.outer_port = outer_port
        self.inner_address_list = inner_address_list
        self.forwarder_address_list = forwarder_address_list
        self.user_redis_url = user_redis_url
        self.user_redis_key_tpl = user_redis_key_tpl
        self.user_redis_maxage = user_redis_maxage
        self.conn_dict = dict()
        self.user_dict = weakref.WeakValueDictionary()
        if self.user_redis_url:
            import redis
            self.user_redis = redis.from_url(self.user_redis_url)

        if debug is not None:
            self.debug = debug

        workers = len(self.inner_address_list)

        def run_wrapper():
            logger.info('Running outer_host: %s, outer_port: %s, input_address_list: %s, output_address_list: %s, debug: %s, workers: %s',
                        outer_host, outer_port,
                        inner_address_list,
                        forwarder_address_list,
                        self.debug, workers)

            self._prepare_server()
            setproctitle.setproctitle(self._make_proc_name('dispatcher:master'))
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

    def _prepare_server(self):
        """
        准备server，因为fork之后就晚了
        :return:
        """
        self.outer_server._prepare_server((self.outer_host, self.outer_port))

    def _serve_forever(self):
        """
        保持运行
        :return:
        """
        job_list = []
        for action in [self.outer_server._serve_forever, self._fetch_forwarders, self._send_task_to_worker]:
            job = gevent.spawn(action)
            job_list.append(job)

        for job in job_list:
            job.join()

    def _start_inner_server(self, address):
        """
        zmq的内部server
        每个worker绑定的地址都要不一样
        """
        ctx = zmq.Context()
        self.zmq_inner_server = ctx.socket(zmq.PUSH)
        self.zmq_inner_server.bind(address)

    def _fetch_forwarders(self):
        """
        从forwarder server那拿数据
        :return:
        """

        ctx = zmq.Context()
        self.zmq_forwarder_client = ctx.socket(zmq.SUB)
        for address in self.forwarder_address_list:
            self.zmq_forwarder_client.connect(address)
        self.zmq_forwarder_client.setsockopt(zmq.SUBSCRIBE, self.worker_uuid)

        while True:
            topic, msg = self.zmq_forwarder_client.recv_multipart()

            task = gw_pb2.Task()
            task.ParseFromString(msg)

            logger.debug('task:\n%s', task)

            # 这样就不会内存泄露了
            job = gevent.spawn(self._deal_task, task)
            job.join()

    def _deal_task(self, task):
        """
        处理task
        :param task:
        :return:
        """

        if task.cmd == constants.CMD_WRITE_TO_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            if conn:
                conn.write(task.data)
        elif task.cmd == constants.CMD_WRITE_TO_WORKER:
            # 重新转发处理
            self.task_queue.put(task)
        elif task.cmd == constants.CMD_CLOSE_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            if conn:
                conn.close()
        elif task.cmd == constants.CMD_LOGIN_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            if conn:
                if conn.uid is not None:
                    # 旧的登录用户

                    # 先从存储删掉
                    if self.user_redis:
                        self.user_redis.delete(self.user_redis_key_tpl % conn.uid)

                    self.user_dict.pop(conn.uid, None)
                    conn.uid = conn.userdata = None

                conn.uid = task.uid
                conn.userdata = task.userdata
                self.user_dict[conn.uid] = conn

                # 后写入存储
                if self.user_redis:
                    self.user_redis.set(self.user_redis_key_tpl % conn.uid, self.worker_uuid, ex=self.user_redis_maxage)

        elif task.cmd == constants.CMD_LOGOUT_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            if conn:
                if conn.uid is not None:
                    if self.user_redis:
                        self.user_redis.delete(self.user_redis_key_tpl % conn.uid)

                    self.user_dict.pop(conn.uid, None)
                    conn.uid = conn.userdata = None

        elif task.cmd == constants.CMD_WRITE_TO_USERS:
            rsp = gw_pb2.RspToUsers()
            rsp.ParseFromString(task.data)

            for row in rsp.rows:
                for uid in row.uids:
                    conn = self.user_dict.get(uid)
                    if conn and (conn.userdata & row.userdata) == row.userdata:
                        conn.write(row.buf)

        elif task.cmd == constants.CMD_CLOSE_USERS:
            rsp = gw_pb2.CloseUsers()
            rsp.ParseFromString(task.data)

            for uid in rsp.uids:

                conn = self.user_dict.get(uid)
                if conn and (conn.userdata & rsp.userdata) == rsp.userdata:
                    conn.close()

    def _send_task_to_worker(self):
        """
        将任务发送到worker
        :return:
        """

        while True:
            task = self.task_queue.get()
            self.zmq_inner_server.send(task.SerializeToString())

    def _register_outer_server_handlers(self):
        """
        注册server的一些回调
        :return:
        """

        @self.outer_server.create_conn
        def create_conn(conn):
            logger.debug('conn.id: %r', conn.id)
            self.conn_dict[conn.id] = conn

            task = gw_pb2.Task()
            task.proc_id = self.worker_uuid
            task.client_id = conn.id
            task.client_ip = conn.address[0]
            task.cmd = constants.CMD_CLIENT_CREATED

            self.task_queue.put(task)

        @self.outer_server.close_conn
        def close_conn(conn):
            # 删除
            logger.debug('conn.id: %r', conn.id)
            self.conn_dict.pop(conn.id, None)
            if conn.uid is not None:
                if self.user_redis:
                    self.user_redis.delete(self.user_redis_key_tpl % conn.uid)

                self.user_dict.pop(conn.uid, None)
                conn.uid = conn.userdata = None

            task = gw_pb2.Task()
            task.proc_id = self.worker_uuid
            task.client_id = conn.id
            task.client_ip = conn.address[0]
            task.cmd = constants.CMD_CLIENT_CLOSED

            self.task_queue.put(task)

        @self.outer_server.handle_request
        def handle_request(conn, data):
            # 转发到worker
            logger.debug('conn.id: %r, data: %r', conn.id, data)
            task = gw_pb2.Task()
            task.proc_id = self.worker_uuid
            task.client_id = conn.id
            task.client_ip = conn.address[0]
            task.cmd = constants.CMD_CLIENT_REQ
            task.data = data
            self.task_queue.put(task)

    def _worker_run(self, index):
        """
        在worker里面执行的
        :return:
        """
        setproctitle.setproctitle(self._make_proc_name('dispatcher:worker:%s' % index))
        self.worker_uuid = uuid.uuid4().bytes
        self._handle_child_proc_signals()
        self._register_outer_server_handlers()
        self._start_inner_server(self.inner_address_list[index])

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