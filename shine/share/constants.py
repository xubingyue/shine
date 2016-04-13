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


# write_to_users / close_users 时的特殊连接集合
CONNS_AUTHED                = -1 # 所有已登录连接
CONNS_ALL                   = -2 # 所有连接
CONNS_UNAUTHED              = -3 # 所有未登录连接


# worker的env
WORKER_ENV_KEY = 'SHINE_WORKER'


# 默认config参数
DEFAULT_CONFIG = {
    # 进程名
    'NAME': NAME,

    # gateway, worker, forwarder 需要
    'DEBUG': False,

    # box class
    'BOX_CLASS': 'netkit.box.Box',

    # gateway 需要
    'GATEWAY_OUTER_HOST': None,
    # gateway 需要
    'GATEWAY_OUTER_PORT': None,
    # gateway 需要
    'GATEWAY_BACKLOG': 256,

    # gateway 需要
    'GATEWAY_CLIENT_HEARTBEAT_CMD': None,  # 客户端心跳的命令字，redis通过这个cmd来进行续期

    # gateway 需要
    'GATEWAY_CLIENT_TIMEOUT': None,  # 客户端连接最长不活跃时间，超过会被关闭。可以设置长一点，因为正常的关闭连接可以被检测到的。

    # gateway, worker 需要
    'GATEWAY_INNER_ADDRESS_LIST': None,

    # worker, forwarder 需要
    'FORWARDER_INPUT_ADDRESS_LIST': None,
    # gateway, forwarder 需要
    'FORWARDER_OUTPUT_ADDRESS_LIST': None,

    # worker 需要
    'WORKER_SPAWN_COUNT': 1,  # 启动多少worker

    # worker 需要
    'WORKER_RSP_ONCE': True,  # worker只能回应一次

    # worker 需要
    'WORKER_CONN_TIMEOUT': 3,  # 连接超时(秒)，比如recv一次的超时

    # worker 需要
    'WORKER_WORK_TIMEOUT': None,  # 处理超时

    # worker 需要
    'WORKER_STOP_TIMEOUT': None,  # 停止进程超时

    # gateway, forwarder 需要
    'REDIS_URL': None,  # 用来存储用户ID->node_id的映射 以及 node_id的集合
    # gateway, forwarder 需要
    'REDIS_KEY_SHARE_PREFIX': NAME + ':',  # 存储的key的统一前缀
    # gateway, forwarder 需要
    'REDIS_USER_KEY_PREFIX': 'user:',  # 存储的user键前缀
    # gateway 需要
    'REDIS_USER_MAX_AGE': None,  # user最长存储的秒数，因为有可能有些用户的数据没有正常清空
    # gateway, forwarder 需要
    'REDIS_NODES_KEY': 'nodes',  # 存储node_id的集合
}
