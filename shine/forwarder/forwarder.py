# -*- coding: utf-8 -*-


import random
import signal
import sys
import setproctitle
import gevent
from gevent.queue import Queue
import zmq.green as zmq  # for gevent
from collections import defaultdict
from ..share.proc_mgr import ProcMgr
from ..share.log import logger
from ..share import constants, shine_pb2
from ..share.config import ConfigAttribute, Config
from ..share.share_store import ShareStore


class Forwarder(object):
    ############################## configurable begin ##############################

    name = ConfigAttribute('NAME')
    debug = ConfigAttribute('DEBUG')

    ############################## configurable end   ##############################

    config = None

    proc_mgr = None
    input_server = None
    output_server = None

    # 等待处理的队列[data, ]
    to_deal_queue = None
    # 等待发送的队列[(topic, data or task), ]
    to_send_queue = None

    share_store = None

    def __init__(self):
        self.config = Config(defaults=constants.DEFAULT_CONFIG)
        self.proc_mgr = ProcMgr()
        self.to_deal_queue = Queue()
        self.to_send_queue = Queue()

    def run(self, debug=None):
        """
        启动
        :param debug: 是否debug
        :return:
        """

        assert len(self.config['FORWARDER_INPUT_ADDRESS_LIST']) == len(self.config['FORWARDER_OUTPUT_ADDRESS_LIST'])

        if self.config['REDIS_URL']:
            import redis
            rds = redis.from_url(self.config['REDIS_URL'])
            self.share_store = ShareStore(rds,
                                          self.config['REDIS_KEY_SHARE_PREFIX'] + self.config['REDIS_USER_KEY_PREFIX'],
                                          self.config['REDIS_KEY_SHARE_PREFIX'] + self.config['REDIS_NODES_KEY'],
                                          self.config['REDIS_USER_MAX_AGE']
                                          )

        if debug is not None:
            self.debug = debug

        workers = len(self.config['FORWARDER_INPUT_ADDRESS_LIST'])

        def run_wrapper():
            logger.info('Running server, debug: %s, workers: %s',
                        self.debug, workers)

            setproctitle.setproctitle(self._make_proc_name('forwarder:master'))
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

    def _handle_task_forever(self):
        """
        一直在处理
        :return:
        """

        while 1:
            data = self.to_deal_queue.get()

            task = shine_pb2.Task()
            task.ParseFromString(data)

            logger.debug('task:\n%s', task)

            if task.cmd in (constants.CMD_WRITE_TO_CLIENT,
                            constants.CMD_LOGIN_CLIENT,
                            constants.CMD_LOGOUT_CLIENT,
                            constants.CMD_CLOSE_CLIENT):
                # 原样处理过去
                # 给data的好处是，就不用再序列化了
                self.to_send_queue.put((task.node_id, data))
            elif task.cmd == constants.CMD_WRITE_TO_WORKER:
                if task.HasField('node_id'):
                    self.to_send_queue.put((task.node_id, data))
                else:
                    # 随机选择一个node_id
                    node_id_list = self.share_store.get_nodes()
                    if node_id_list:
                        self.to_send_queue.put((random.choice(list(node_id_list)), data))
                    else:
                        logger.error('node_id_list is empty.')

            elif task.cmd == constants.CMD_WRITE_TO_USERS:
                if not self.share_store:
                    # 直接转发就好
                    self.to_send_queue.put((task.node_id, data))
                else:
                    # 这个是所有row合并在一起的uid_list，是为了快速获取node_id而用的
                    merged_uid_list = set()
                    rsp = shine_pb2.RspToUsers()
                    rsp.ParseFromString(task.body)
                    for row in rsp.rows:
                        merged_uid_list.update(set(row.uids))

                    merged_uid_list = list(merged_uid_list)  # 一定要变回来

                    node_id_to_uid_dict = self.share_store.get_users(merged_uid_list)

                    node_id_to_rsp_dict = defaultdict(shine_pb2.RspToUsers)

                    for row in rsp.rows:
                        node_id_to_row_dict = dict()

                        uid_list = row.uids
                        if set((constants.CONNS_AUTHED, constants.CONNS_ALL, constants.CONNS_UNAUTHED)) & set(uid_list):
                            # 给所有的topic都发一遍就好
                            node_id_list = self.share_store.get_nodes()
                            for node_id in node_id_list:
                                # 所有proc都要收到这个消息并进行处理
                                node_id_to_rsp_dict[node_id].rows.extend([row])

                            # 直接跳到下一个row
                            continue

                        for uid in uid_list:
                            node_id = node_id_to_uid_dict.get(uid)
                            if node_id is None:
                                continue

                            if node_id not in node_id_to_row_dict:
                                new_row = shine_pb2.RspToUsers.Row()
                                new_row.userdata = row.userdata
                                new_row.buf = row.buf
                                node_id_to_row_dict[node_id] = new_row
                            else:
                                new_row = node_id_to_row_dict[node_id]

                            new_row.uids.append(uid)

                        for node_id, new_row in node_id_to_row_dict.items():
                            # 得用extend才行
                            node_id_to_rsp_dict[node_id].rows.extend([new_row])

                    # 消息已经搞定了，现在就是发送了
                    for node_id, rsp in node_id_to_rsp_dict.items():
                        rsp_task = shine_pb2.Task()
                        rsp_task.cmd = task.cmd
                        rsp_task.node_id = node_id
                        rsp_task.body = rsp.SerializeToString()

                        self.to_send_queue.put((node_id, rsp_task))
            elif task.cmd == constants.CMD_CLOSE_USERS:
                if not self.share_store:
                    # 直接转发就好
                    self.to_send_queue.put((task.node_id, data))
                else:
                    node_id_to_rsp_dict = defaultdict(shine_pb2.CloseUsers)

                    rsp = shine_pb2.CloseUsers()
                    rsp.ParseFromString(task.body)

                    merged_uid_list = list(rsp.uids)

                    if set((constants.CONNS_AUTHED, constants.CONNS_ALL, constants.CONNS_UNAUTHED)) & set(merged_uid_list):
                        # 给所有的topic都发一遍就好
                        node_id_list = self.share_store.get_nodes()
                        for node_id in node_id_list:
                            # 所有proc都要收到这个消息并进行处理
                            node_id_to_rsp_dict[node_id] = rsp
                    else:
                        node_id_to_uid_dict = self.share_store.get_users(merged_uid_list)

                        for uid in merged_uid_list:
                            node_id = node_id_to_uid_dict.get(uid)
                            if node_id is None:
                                continue

                            if node_id not in node_id_to_rsp_dict:
                                new_rsp = shine_pb2.CloseUsers()
                                new_rsp.userdata = rsp.userdata
                                node_id_to_rsp_dict[node_id] = new_rsp
                            else:
                                new_rsp = node_id_to_rsp_dict[node_id]

                            new_rsp.uids.append(uid)

                    # 消息已经搞定了，现在就是发送了
                    for node_id, rsp in node_id_to_rsp_dict.items():
                        rsp_task = shine_pb2.Task()
                        rsp_task.cmd = task.cmd
                        rsp_task.node_id = node_id
                        rsp_task.body = rsp.SerializeToString()

                        self.to_send_queue.put((node_id, rsp_task))

    def _handle_input_forever(self):
        """
        一直在收消息
        :return:
        """

        while 1:
            data = self.input_server.recv()

            self.to_deal_queue.put(data)

    def _handle_output_forever(self):
        """
        :return:
        """
        while 1:
            topic, data = self.to_send_queue.get()
            if isinstance(data, shine_pb2.Task):
                data = data.SerializeToString()

            self.output_server.send_multipart(
                (topic, data)
            )

    def _serve_forever(self):
        """
        保持运行
        :return:
        """
        job_list = []
        for action in [self._handle_input_forever, self._handle_task_forever, self._handle_output_forever]:
            job = gevent.spawn(action)
            job_list.append(job)

        for job in job_list:
            job.join()

    def _start_input_server(self, address):
        """
        zmq的pull server
        每个worker绑定的地址都要不一样
        """
        ctx = zmq.Context()
        self.input_server = ctx.socket(zmq.PULL)
        self.input_server.bind(address)

    def _start_output_server(self, address):
        """
        zmq的output server
        每个worker绑定的地址都要不一样
        """
        ctx = zmq.Context()
        self.output_server = ctx.socket(zmq.PUB)
        self.output_server.bind(address)

    def _worker_run(self, index):
        """
        在worker里面执行的
        :return:
        """
        setproctitle.setproctitle(self._make_proc_name('forwarder:worker:%s' % index))
        self._handle_child_proc_signals()

        self._start_input_server(self.config['FORWARDER_INPUT_ADDRESS_LIST'][index])
        self._start_output_server(self.config['FORWARDER_OUTPUT_ADDRESS_LIST'][index])

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
