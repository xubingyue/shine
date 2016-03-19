# -*- coding: utf-8 -*-

from multiprocessing import Process
import time


class ProcMgr(object):
    enable = True
    processes = None

    def __init__(self):
        self.processes = []

    def spawn_workers(self, workers, target):
        def start_worker_process(index):
            inner_p = Process(target=target, args=(index,))
            # 当前进程daemon默认是False，改成True将启动不了子进程
            # 但是子进程要设置daemon为True，这样父进程退出，子进程会被强制关闭
            # 现在父进程会在子进程之后推出，没必要设置了
            # inner_p.daemon = True
            inner_p.start()
            return inner_p

        for it in xrange(0, workers):
            p = start_worker_process(it)
            self.processes.append(p)

        while 1:
            for idx, p in enumerate(self.processes):
                if p and not p.is_alive():
                    self.processes[idx] = None

                    if self.enable:
                        p = start_worker_process(idx)
                        self.processes[idx] = p

            if not filter(lambda x: x, self.processes):
                # 没活着的了
                break

            # 时间短点，退出的快一些
            time.sleep(0.1)

    def terminate_all(self):

        # 如果是终端直接CTRL-C，子进程自然会在父进程之后收到INT信号，不需要再写代码发送
        # 如果直接kill -INT $parent_pid，子进程不会自动收到INT
        # 所以这里可能会导致重复发送的问题，重复发送会导致一些子进程异常，所以在子进程内部有做重复处理判断。
        for p in self.processes:
            if p:
                p.terminate()
