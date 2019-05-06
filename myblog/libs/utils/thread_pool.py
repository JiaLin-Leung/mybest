# coding: utf-8
import time
import threading
import queue
import logging
POOL_SIZE = 50
q = queue.Queue()


def loop(id):
    while 1:
        f, args, kwargs = q.get()
        try:
            f(*args, **kwargs)
        except Exception as e:
            logging.error(e)


def call(f, *args, **kwargs):
    q.put((f, args, kwargs))


def init():
    print('thread_pool init.')
    for i in range(POOL_SIZE):
        t = threading.Thread(target=loop, args=(i, ))
        t.start()

init()
