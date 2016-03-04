# -*- coding: utf-8 -*-


GATEWAY_OUTER_HOST = '127.0.0.1'
GATEWAY_OUTER_PORT = 7100

GATEWAY_INNER_ADDRESS_LIST = [
    'tcp://127.0.0.1:7200',
    'tcp://127.0.0.1:7201',
]


FORWARDER_INPUT_ADDRESS_LIST = [
    'tcp://127.0.0.1:7300',
    'tcp://127.0.0.1:7301',
]

FORWARDER_OUTPUT_ADDRESS_LIST = [
    'tcp://127.0.0.1:7400',
    'tcp://127.0.0.1:7401',
]

REDIS_URL = 'redis://127.0.0.1:6379/0'
REDIS_USER_KEY_PREFIX = 'shine:user:'
