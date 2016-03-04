# -*- coding: utf-8 -*-

NAME = 'shine'

# 系统返回码
RET_INVALID_CMD = -10000
RET_INTERNAL = -10001

# 命令字
CMD_CLIENT_REQ              = 10  # 透传client请求
CMD_CLIENT_CREATED          = 15  # 客户端连接建立
CMD_CLIENT_CLOSED           = 20  # 客户端连接被关闭

CMD_WRITE_TO_WORKER         = 100 # trigger触发请求

CMD_WORKER_ASK_FOR_JOB      = 210 # 请求任务

CMD_WRITE_TO_CLIENT         = 220 # 回应
CMD_WRITE_TO_USERS          = 230 # 主动下发
CMD_CLOSE_CLIENT            = 240 # 关闭客户端(client_id为判断)
CMD_CLOSE_USERS             = 250 # 关闭多个客户端
CMD_LOGIN_CLIENT            = 260 # 登录用户
CMD_LOGOUT_CLIENT           = 270 # 登出用户


# worker的env
WORKER_ENV_KEY = 'SHINE_WORKER'


# 默认config参数
DEFAULT_CONFIG = {
    # 进程名
    'NAME': NAME,

    # gateway, worker, forwarder 需要
    'DEBUG': False,

    # gateway 需要
    'GATEWAY_OUTER_HOST': None,
    # gateway 需要
    'GATEWAY_OUTER_PORT': None,
    # gateway 的backlog
    'GATEWAY_BACKLOG': 256,

    # gateway, worker 需要
    'GATEWAY_INNER_ADDRESS_LIST': None,

    # worker, forwarder 需要
    'FORWARDER_INPUT_ADDRESS_LIST': None,
    # gateway, forwarder 需要
    'FORWARDER_OUTPUT_ADDRESS_LIST': None,

    # gateway, forwarder 需要
    'USER_REDIS_URL': None,  # 用来存储用户ID->proc_id的映射
    # gateway, forwarder 需要
    'USER_REDIS_KEY_TPL': '%s',  # 存储的键模板
    # gateway 需要
    'USER_REDIS_MAXAGE': None,  # 最长存储的秒数，因为有可能有些用户的数据没有正常清空
}
