# -*- coding: utf-8 -*-


from gevent import monkey; monkey.patch_all()

import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from zmq_server import Gateway
import constants


gateway = Gateway(Box)

if __name__ == '__main__':
    gateway.run(
        constants.GATEWAY_OUTER_HOST,
        constants.GATEWAY_OUTER_PORT,
        constants.GATEWAY_INNER_ADDRESS_LIST,
        constants.FORWARDER_PUB_ADDRESS_LIST,
        'redis://127.0.0.1:6379/0',
        'zmq:user:%s',
    )
