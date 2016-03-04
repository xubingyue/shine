# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '../../')
from netkit.box import Box
import time
from shine import Trigger

import config


def handle():
    trigger = Trigger(Box, config.FORWARDER_INPUT_ADDRESS_LIST)

    box = Box()
    box.cmd = 3

    trigger.write_to_users([
        [(-1,), box]
    ])


def main():
    handle()

if __name__ == '__main__':
    main()
