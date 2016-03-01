# -*- coding: utf-8 -*-


import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from zmq_server import Worker
import constants


worker = Worker(Box)


@worker.route(2)
def login(request):
    request.write_to_client(dict(
        ret=100,
        body='ok'
    ))


if __name__ == '__main__':
    worker.run(
        constants.GATEWAY_WORKER_ADDRESS_LIST,
        constants.RESULTER_PULL_ADDRESS_LIST,
    )
