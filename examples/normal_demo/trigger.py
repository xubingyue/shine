# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '../../')
from netkit.box import Box
import time
from shine import Trigger
from shine.share import constants

import config


def handle():
    trigger = Trigger(forwarder_input_address_list=config.FORWARDER_INPUT_ADDRESS_LIST)

    box = Box()
    box.cmd = 3

    trigger.write_to_users([
        [(constants.CONNS_AUTHED,), box]
    ])

    box2 = Box()
    box2.cmd = 5
    trigger.write_to_worker(
        box2
    )


def main():
    handle()

if __name__ == '__main__':
    main()
