### shine


### 一. 概述

高性能，分布式服务器框架。支持无限扩容。

灵感来自于 [maple](https://github.com/dantezhu/maple)，这是笔者的另一款高性能服务器框架。主要有如下几点不同:

1. 原生支持分布式用户状态存储，不需要业务层再写代码。
2. 使用zmq作为内部通信组件，快速实现多对多通信，极大增强了可扩展性和稳定性。
3. 纯python编写，不再仅限于linux平台。


### 二. 模块介绍

主要有 gateway、worker、forwarder 三个模块。


1. gateway
    
    连接服务器。
    
    负责客户端连接的接入，使用多进程fork-listen的模型。而每个进程内，使用gevent。
    用户成功连接后，会在不同的node(即进程)上建立连接。同时，client与node的关系数据会同步到redis中存储起来。
    每一个node都有一个唯一的uuid，所以即使不同机器上启动的不同gateway，node也可以唯一标识出来。

    另一方面，每个node都会将从client收到的消息通过zmq.PUSH到worker。

    同时，node也会通过zmq.SUB，从forwarder初监听仅属于自己node_id的消息。


2. worker

    工作服务器。

    一方面，通过 zmq.PULL 从gateway处获取客户单消息。

    另一方面，当消息处理完毕后，将响应按照一定的格式发送到forwarder.

    write_to_users 可以批量发送给多个用户

        # -1: 所有已登录连接
        # -2: 所有连接
        # -3: 所有未登陆连接


3. forwarder

    转发服务器。

    一方面，通过 zmq.PULL 从worker出获取响应。

    另一方面，通过 zmq.PUB 将响应通知给不同 node_id 的node。


4. trigger
    
    触发器。与maple.trigger功能一样，只是实现上不太一样。

    trigger 内部只与 forwarder 进行通信，由forwarder负责消息的转发。

#### 三. TODO

<del>1. 没有对心跳命令字做特殊延期处理</del>
2. 还没有监控请求量和在线量的工具
