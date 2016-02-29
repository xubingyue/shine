# -*- coding: utf-8 -*-

import os
import socket
import thread
import time
import zmq
from ..share import constants, gw_pb2
from ..share.log import logger


class Connection(object):

    job_info = None

    address_list = None
    zmq_client = None

    def __init__(self, app, address_list):
        self.app = app
        self.address_list = address_list

        ctx = zmq.Context()
        self.zmq_client = ctx.socket(zmq.PUSH)
        for address in address_list:
            self.zmq_client.connect(address)

    def run(self):
        thread.start_new_thread(self._monitor_job_timeout, ())
        while 1:
            try:
                self._handle()
            except KeyboardInterrupt:
                break
            except:
                logger.error('exc occur.', exc_info=True)

    def _monitor_job_timeout(self):
        """
        监控job的耗时
        :return:
        """

        while self.app.enable:
            time.sleep(1)

            job_info = self.job_info
            if job_info:
                past_time = time.time() - job_info['begin_time']
                if self.app.job_timeout is not None and past_time > self.app.job_timeout:
                    # 说明worker的处理时间已经太长了
                    logger.error('job is timeout: %s / %s, request: %s',
                                 past_time, self.app.job_timeout, job_info['request'])
                    # 强制从子线程退出worker
                    os._exit(-1)

    def _handle(self):
        if not self.app.enable:
            # 安全退出
            raise KeyboardInterrupt

        self._read_message()

    def write(self, data):
        """
        格式可以支持到frame
        发送数据    True: 成功   else: 失败
        """
        if self.closed():
            logger.error('connection closed. data: %r', data)
            return False

        # 只支持字符串
        self.app.events.before_response(self, data)
        for bp in self.app.blueprints:
            bp.events.before_app_response(self, data)

        ret = self.app.zmq_result_client.send(data)
        if not ret:
            logger.error('connection write fail. data: %r', data)

        for bp in self.app.blueprints:
            bp.events.after_app_response(self, data, ret)
        self.app.events.after_response(self, data, ret)

        return ret

    def _read_message(self):

        msg = self.zmq_client.recv_string()

        task = gw_pb2.Task()
        task.ParseFromString(msg)

        self._on_read_complete(task)

        if self.closed():
            self._on_connection_close()

    def _on_connection_close(self):
        # 链接被关闭的回调

        logger.error('connection closed, address_list: %s', self.address_list)

        for bp in self.app.blueprints:
            bp.events.close_app_conn(self)
        self.app.events.close_conn(self)

    def _on_read_complete(self, data):
        """
        数据获取结束
        """
        request = self.app.request_class(self, data)

        # 设置job开始处理的时间和信息
        self.job_info = dict(
            begin_time=time.time(),
            request=request,
        )
        self._handle_request(request)
        self.job_info = None

    def _handle_request(self, request):
        """
        出现任何异常的时候，服务器不再主动关闭连接
        """

        if not request.is_valid:
            return False

        if request.gw_box.cmd == constants.CMD_CLIENT_CREATED:
            self.app.events.create_client(request)
            for bp in self.app.blueprints:
                bp.events.create_app_client(request)
            return True
        elif request.gw_box.cmd == constants.CMD_CLIENT_CLOSED:
            self.app.events.close_client(request)
            for bp in self.app.blueprints:
                bp.events.close_app_client(request)
            return True

        if not request.view_func:
            logger.info('cmd invalid. request: %s' % request)
            if not request.responded:
                request.write_to_client(dict(ret=constants.RET_INVALID_CMD))
            return False

        if not self.app.got_first_request:
            self.app.got_first_request = True
            self.app.events.before_first_request(request)
            for bp in self.app.blueprints:
                bp.events.before_app_first_request(request)

        self.app.events.before_request(request)
        for bp in self.app.blueprints:
            bp.events.before_app_request(request)
        if request.blueprint:
            request.blueprint.events.before_request(request)

        if request.interrupted:
            # 业务要求中断
            return True

        view_func_exc = None

        try:
            request.view_func(request)
        except Exception, e:
            logger.error('view_func raise exception. request: %s, e: %s',
                         request, e, exc_info=True)
            view_func_exc = e
            # 必须是没有回应过
            if not request.responded:
                request.write_to_client(dict(ret=constants.RET_INTERNAL))

        if request.blueprint:
            request.blueprint.events.after_request(request, view_func_exc)
        for bp in self.app.blueprints:
            bp.events.after_app_request(request, view_func_exc)
        self.app.events.after_request(request, view_func_exc)

        return True

    def close(self):
        """
        直接关闭连接
        """
        self.zmq_client.close()

    def closed(self):
        """
        连接是否已经关闭
        :return:
        """
        return self.zmq_client.closed
