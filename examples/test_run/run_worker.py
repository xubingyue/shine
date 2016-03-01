# -*- coding: utf-8 -*-


import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from zmq_server import Worker, logger
import constants


worker = Worker(Box)


@worker.create_client
def create_client(request):
    logger.debug(request)


@worker.close_client
def close_client(request):
    logger.debug(request)


@worker.route(2)
def login(request):
    request.login_client(1, 2)
    # request.logout_client()
    request.write_to_client(dict(
        ret=100,
        body='ok'
    ))


@worker.route(3)
def write_to_users(request):
    request.write_to_users([
        ((1, 2), dict(
            ret=0,
            body='from worker'
        )),
    ])
    request.write_to_client(dict(
        ret=100,
        body='ok'
    ))


@worker.route(4)
def close_users(request):
    request.close_users([1, 2])
    request.write_to_client(dict(
        ret=100,
        body='ok'
    ))

if __name__ == '__main__':
    worker.run(
        constants.GATEWAY_INNER_ADDRESS_LIST,
        constants.FORWARDER_PULL_ADDRESS_LIST,
    )
