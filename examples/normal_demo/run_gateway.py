# -*- coding: utf-8 -*-


from gevent import monkey; monkey.patch_all()

import sys
sys.path.insert(0, '../../')

from netkit.box import Box
from shine import Gateway
import constants


gateway = Gateway(Box)
gateway.config.from_object(constants)

if __name__ == '__main__':
    gateway.run()
