# -*- coding: utf-8 -*-

"""
接收客户端连接，并派发消息给worker
"""


from netkit.box import Box
from zmq_server import Gateway


gateway = Gateway(Box)

if __name__ == '__main__':
    gateway.run(
        ('127.0.0.1', 7100),
        ('127.0.0.1', 7101),
        ('127.0.0.1', 7102),
    )
