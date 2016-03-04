# -*- coding: utf-8 -*-

import logging
import constants
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
logger = logging.getLogger(constants.NAME)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
