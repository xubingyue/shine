# -*- coding: utf-8 -*-


GATEWAY_OUTER_HOST = '127.0.0.1'
GATEWAY_OUTER_PORT = 7100

GATEWAY_CLIENT_TIMEOUT = 300

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

import logging
import colorlog


LOG_FORMAT = '\n'.join((
    '/' + '-' * 80,
    '[%(levelname)s][%(asctime)s][%(process)d:%(thread)d][%(filename)s:%(lineno)d %(funcName)s]:',
    '%(message)s',
    '-' * 80 + '/',
))

COLOR_LOG_FORMAT = '%(log_color)s' + LOG_FORMAT

handler = logging.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(COLOR_LOG_FORMAT, log_colors={
    'DEBUG':    'cyan',
    'INFO':     'green',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'red',
}))
logger = logging.getLogger('shine')
logger.addHandler(handler)
logger.setLevel(logging.ERROR)
