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
from ..share import constants, shine_pb2
from ..share.config import ConfigAttribute, Config
from ..share.share_store import ShareStore
from ..share.utils import import_module_or_string


class Gateway(object):
    ############################## configurable begin ##############################

    box_class = ConfigAttribute('BOX_CLASS',
                                get_converter=import_module_or_string)
    name = ConfigAttribute('NAME')
    debug = ConfigAttribute('DEBUG')

    ############################## configurable end   ##############################

    config = None

    proc_mgr = None
    outer_server = None
    inner_server = None
    forwarder_client = None

    # 准备发送到worker的queue
    task_queue = None

    # worker唯一标示
    node_id = None
    # 连接ID->conn
    conn_dict = None
    # 用户ID->conn
    user_dict = None

    # 共享存储
    share_store = None

    def __init__(self):
        self.config = Config(defaults=constants.DEFAULT_CONFIG)
        self.proc_mgr = ProcMgr()
        self.task_queue = Queue()
        self.conn_dict = dict()
        self.user_dict = weakref.WeakValueDictionary()

    def run(self, debug=None):
        """
        启动
        :param debug: 是否debug
        :return:
        """

        if debug is not None:
            self.debug = debug

        # 要在run的时候，才创建
        self.outer_server = Server(self.box_class,
                                   self.config['GATEWAY_BACKLOG'],
                                   self.config['GATEWAY_CLIENT_TIMEOUT']
                                   )

        if self.config['REDIS_URL']:
            import redis
            rds = redis.from_url(self.config['REDIS_URL'])
            self.share_store = ShareStore(rds,
                                          self.config['REDIS_KEY_SHARE_PREFIX'] + self.config['REDIS_USER_KEY_PREFIX'],
                                          self.config['REDIS_KEY_SHARE_PREFIX'] + self.config['REDIS_NODES_KEY'],
                                          self.config['REDIS_USER_MAX_AGE']
                                          )

        workers = len(self.config['GATEWAY_INNER_ADDRESS_LIST'])

        def run_wrapper():
            logger.info('Running server, debug: %s, workers: %s',
                        self.debug, workers)

            self._prepare_server()
            setproctitle.setproctitle(self._make_proc_name('gateway:master'))
            # 只能在主线程里面设置signals
            self._handle_parent_proc_signals()
            self.proc_mgr.spawn_workers(workers, self._worker_run)

        run_wrapper()

    def _make_proc_name(self, subtitle):
        """
        获取进程名称
        :param subtitle:
        :return:
        """
        proc_name = '[%s:%s %s] %s' % (
            constants.NAME,
            subtitle,
            self.name,
            ' '.join([sys.executable] + sys.argv)
        )

        return proc_name

    def _make_redis_key(self, uid):
        return self.config['REDIS_KEY_SHARE_PREFIX'] + self.config['REDIS_USER_KEY_PREFIX'] + str(uid)

    def _prepare_server(self):
        """
        准备server，因为fork之后就晚了
        :return:
        """
        self.outer_server._prepare_server((self.config['GATEWAY_OUTER_HOST'], self.config['GATEWAY_OUTER_PORT']))

    def _serve_forever(self):
        """
        保持运行
        :return:
        """
        job_list = []
        for action in [self.outer_server._serve_forever, self._fetch_from_forwarder, self._send_task_to_worker]:
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
        self.inner_server = ctx.socket(zmq.PUSH)
        self.inner_server.bind(address)

    def _fetch_from_forwarder(self):
        """
        从forwarder server那拿数据
        :return:
        """

        ctx = zmq.Context()
        self.forwarder_client = ctx.socket(zmq.SUB)
        for address in self.config['FORWARDER_OUTPUT_ADDRESS_LIST']:
            self.forwarder_client.connect(address)
        self.forwarder_client.setsockopt(zmq.SUBSCRIBE, self.node_id)

        while True:
            topic, msg = self.forwarder_client.recv_multipart()

            task = shine_pb2.Task()
            task.ParseFromString(msg)

            logger.debug('task:\n%s', task)

            # 这样就不会内存泄露了
            job = gevent.spawn(self._handle_task, task)
            job.join()

    def _handle_task(self, task):
        """
        处理task
        :param task:
        :return:
        """

        if task.cmd == constants.CMD_WRITE_TO_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            if conn:
                conn.write(task.body)
        elif task.cmd == constants.CMD_WRITE_TO_WORKER:
            # 重新转发处理
            # 标记一下
            task.inner = 1
            self.task_queue.put(task)
        elif task.cmd == constants.CMD_CLOSE_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            if conn:
                conn.close()
        elif task.cmd == constants.CMD_LOGIN_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            self._login_client(conn, task.uid, task.userdata)

        elif task.cmd == constants.CMD_LOGOUT_CLIENT:
            conn = self.conn_dict.get(task.client_id)
            self._logout_client(conn)

        elif task.cmd == constants.CMD_WRITE_TO_USERS:
            rsp = shine_pb2.RspToUsers()
            rsp.ParseFromString(task.body)

            for row in rsp.rows:
                if constants.CONNS_AUTHED in row.uids:
                    for conn in self.conn_dict.values():
                        if conn and conn.uid and (conn.userdata & row.userdata) == row.userdata:
                            conn.write(row.buf)
                elif constants.CONNS_ALL in row.uids:
                    for conn in self.conn_dict.values():
                        if conn and (conn.userdata & row.userdata) == row.userdata:
                            conn.write(row.buf)
                elif constants.CONNS_UNAUTHED in row.uids:
                    for conn in self.conn_dict.values():
                        if conn and not conn.uid and (conn.userdata & row.userdata) == row.userdata:
                            conn.write(row.buf)
                else:
                    for uid in row.uids:
                        conn = self.user_dict.get(uid)
                        if conn and (conn.userdata & row.userdata) == row.userdata:
                            conn.write(row.buf)

        elif task.cmd == constants.CMD_CLOSE_USERS:
            rsp = shine_pb2.CloseUsers()
            rsp.ParseFromString(task.body)

            if constants.CONNS_AUTHED in rsp.uids:
                for conn in self.conn_dict.values():
                    if conn and conn.uid and (conn.userdata & rsp.userdata) == rsp.userdata:
                        conn.close()
            elif constants.CONNS_ALL in rsp.uids:
                for conn in self.conn_dict.values():
                    if conn and (conn.userdata & rsp.userdata) == rsp.userdata:
                        conn.close()
            elif constants.CONNS_UNAUTHED in rsp.uids:
                for conn in self.conn_dict.values():
                    if conn and not conn.uid and (conn.userdata & rsp.userdata) == rsp.userdata:
                        conn.close()
            else:
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
            self.inner_server.send(task.SerializeToString())

    def _register_outer_server_handlers(self):
        """
        注册server的一些回调
        :return:
        """

        @self.outer_server.create_conn
        def create_conn(conn):
            logger.debug('conn.id: %r', conn.id)
            self.conn_dict[conn.id] = conn

            task = shine_pb2.Task()
            task.node_id = self.node_id
            task.client_id = conn.id
            task.client_ip = conn.address[0]
            task.uid = conn.uid
            task.userdata = conn.userdata
            task.cmd = constants.CMD_CLIENT_CREATED

            self.task_queue.put(task)

        @self.outer_server.close_conn
        def close_conn(conn):
            # 删除
            logger.debug('conn.id: %r', conn.id)

            task = shine_pb2.Task()
            task.node_id = self.node_id
            task.client_id = conn.id
            task.client_ip = conn.address[0]
            task.uid = conn.uid
            task.userdata = conn.userdata
            task.cmd = constants.CMD_CLIENT_CLOSED

            self.conn_dict.pop(conn.id, None)
            # 尝试退出登录
            self._logout_client(conn)

            self.task_queue.put(task)

        @self.outer_server.handle_request
        def renew_user(conn, box):
            """
            检查是否是心跳，如果是则进行续期
            """
            if self.share_store:
                if conn.uid and box.cmd == self.config['GATEWAY_CLIENT_HEARTBEAT_CMD']:
                    # 说明是心跳
                    gevent.spawn(self.share_store.renew_user, conn.uid)

        @self.outer_server.handle_request
        def handle_request(conn, box):
            # 转发到worker
            logger.debug('conn.id: %r, box: %s', conn.id, box)
            task = shine_pb2.Task()
            task.node_id = self.node_id
            task.client_id = conn.id
            task.client_ip = conn.address[0]
            task.uid = conn.uid
            task.userdata = conn.userdata
            task.cmd = constants.CMD_CLIENT_REQ
            # 原始数据
            task.body = box._raw_data
            self.task_queue.put(task)

    def _worker_run(self, index):
        """
        在worker里面执行的
        :return:
        """
        setproctitle.setproctitle(self._make_proc_name('gateway:worker:%s' % index))
        self.node_id = uuid.uuid4().bytes
        if self.share_store:
            self.share_store.add_node(self.node_id)
        self._handle_child_proc_signals()
        self._register_outer_server_handlers()
        self._start_inner_server(self.config['GATEWAY_INNER_ADDRESS_LIST'][index])

        try:
            self._serve_forever()
        except KeyboardInterrupt:
            if self.share_store:
                self.share_store.remove_node(self.node_id)
            pass
        except:
            logger.error('exc occur.', exc_info=True)

    def _login_client(self, conn, uid, userdata):
        if conn and conn.uid != uid:
            self._logout_client(conn)

            conn.uid = uid
            conn.userdata = userdata
            self.user_dict[conn.uid] = conn

            # 后写入存储
            if self.share_store:
                gevent.spawn(self.share_store.add_user, conn.uid, self.node_id)

    def _logout_client(self, conn):
        if conn and conn.uid is not None:
            if self.share_store:
                gevent.spawn(self.share_store.remove_user, conn.uid, self.node_id)

            self.user_dict.pop(conn.uid, None)
            conn.uid = conn.userdata = 0

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
