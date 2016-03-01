# -*- coding: utf-8 -*-


from gevent import monkey; monkey.patch_all()

import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from zmq_server import Dispatcher
import constants


dispatcher = Dispatcher(Box)

if __name__ == '__main__':
    dispatcher.run(
        constants.DISPATCHER_OUTER_HOST,
        constants.DISPATCHER_OUTER_PORT,
        constants.DISPATCHER_INNER_ADDRESS_LIST,
        constants.FORWARDER_PUB_ADDRESS_LIST,
        'redis://127.0.0.1:6379/0',
        'zmq:user:%s',
    )