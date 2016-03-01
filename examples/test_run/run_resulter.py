# -*- coding: utf-8 -*-

from gevent import monkey; monkey.patch_all()

import sys
sys.path.insert(0, '../../')

from zmq_server import Resulter
import constants


resulter = Resulter()

if __name__ == '__main__':
    resulter.run(
        constants.RESULTER_PULL_ADDRESS_LIST,
        constants.RESULTER_PUB_ADDRESS_LIST,
    )
