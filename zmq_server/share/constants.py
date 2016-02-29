# -*- coding: utf-8 -*-

NAME = 'zmq_server'

# 系统返回码
RET_INVALID_CMD = -10000
RET_INTERNAL = -10001

# 默认host和port
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 7777
SERVER_BACKLOG = 256


# 客户端连接创建
CMD_CLIENT_CREATED = 1
# 客户端连接关闭
CMD_CLIENT_CLOSED = 2

# 客户端请求
CMD_CLIENT_REQ = 100
