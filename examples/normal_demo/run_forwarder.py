# -*- coding: utf-8 -*-

from gevent import monkey; monkey.patch_all()

import sys
sys.path.insert(0, '../../')

from shine import Forwarder
import constants


forwarder = Forwarder()
forwarder.config.from_object(constants)

if __name__ == '__main__':
    forwarder.run()
