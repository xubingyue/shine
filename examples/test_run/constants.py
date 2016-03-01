# -*- coding: utf-8 -*-


GATEWAY_OUTER_HOST = '127.0.0.1'
GATEWAY_OUTER_PORT = 7100

GATEWAY_WORKER_ADDRESS_LIST = [
    'tcp://127.0.0.1:7200',
    'tcp://127.0.0.1:7201',
]


FORWARDER_PULL_ADDRESS_LIST = [
    'tcp://127.0.0.1:7300',
    'tcp://127.0.0.1:7301',
]

FORWARDER_PUB_ADDRESS_LIST = [
    'tcp://127.0.0.1:7400',
    'tcp://127.0.0.1:7401',
]
