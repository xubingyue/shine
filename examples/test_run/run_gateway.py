# -*- coding: utf-8 -*-


from gevent import monkey; monkey.patch_all()

import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from zmq_server import Gateway


gateway = Gateway(Box)

if __name__ == '__main__':
    gateway.run(
        '127.0.0.1', 7100,
        ['tcp://127.0.0.1:7101', 'tcp://127.0.0.1:7102'],
        'tcp://127.0.0.1:7201',
    )
