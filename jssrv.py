#!/usr/bin/env python
# coding=utf-8


import logging
import os
import commands
import sys
import threading
import time
import traceback
import tornado
import tornado.httpserver
import tornado.web
import tornado.ioloop

from phantomjsservice.phantomjspool import PhantomJSPool
from phantomjsservice.service import PhantomJSHandler, StopServiceHandler
from phantomjsservice.config import *
from tools.common import warning_title_phantomjs, warning_text_phantomjs
from tools.logger import Logger
from tools.warning import WarningMsg


MAIN_PROCESS = ''
MAIN_PROCESS_PID = ''
JS_PID = []
logger = None


def webapplication():
    handlers = [(r'/eleven', PhantomJSHandler),
                (r'/stop', StopServiceHandler)
                ]
    return tornado.web.Application(handlers)


if __name__ == '__main__':
    if len(sys.argv) - 1 < 1:
        print 'Please give some params for service launching... such as [python app.py num_threadpool=10 num_js=10 log_path=/usr/local/log]'
        sys.exit(-1)

    thread_name = threading.currentThread().name
    app_startup_path = os.path.dirname(os.path.realpath(__file__))

    # params
    MAIN_PROCESS = sys.argv[0][sys.argv[0].rfind(r'/') + 1:]
    settings = {'parent_process': MAIN_PROCESS}
    params = sys.argv[0:]
    for p in params[1:]:
        name = p.split('=')[0].strip(' ')
        if name == 'num_jspool':
            set_jspool(int(p.split('=')[1].strip(' ')))
        elif name == 'num_proxy_ip':
            set_proxy_ip(int(p.split('=')[1].strip(' ')))
        elif name == 'log_path':
            LOG_PATH = p.split('=')[1].strip(' ')

    logger = Logger.getlogger(level=logging.DEBUG, name=LOG_NAME, path=LOG_PATH)
    logger.info('<<<========================= PhantomJS Service This log starting at %s =========================>>>', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    logger.info('Thread: %s, num_threadpool=%s', thread_name, NUM_THREADPOOL)
    logger.info('Thread: %s, num_phantomjspool=%s', thread_name, get_jspool())
    # logger.info('Thread: %s, num_proxy_ip=%s', thread_name, get_proxy_ip())

    # start threading to update network PROXY
    # thread_proxy_daemon = FixProxy()
    # thread_proxy_daemon.name = 'thread_proxy_daemon'
    # thread_proxy_daemon.setDaemon(True)
    # thread_proxy_daemon.start()
    # logger.info('Thread: %s, thread_proxy_daemon start... please waiting for few minutes...', thread_name)

    # create phantomjs pool
    JS_PID = PhantomJSPool.init(num=get_jspool())
    logger.info('Thread: %s, phantomjs pool has been created, %s process, PID: %s', thread_name, get_jspool(), JS_PID)

    # save PID
    # set_pid(MAIN_PROCESS_PID, JS_PID)

    # start threading to checking defunct process
    # thread_phantomjs_daemon = PhantomJSDaemon(NUM_PHANTOMJS_POOL)
    # thread_phantomjs_daemon.name = 'thread_js_daemon'
    # thread_phantomjs_daemon.setDaemon(True)
    # thread_phantomjs_daemon.start()
    # logger.info('Thread: %s, thread_js_daemon start...', thread_name)

    # start service
    logger.info('Thread: %s, Start phantomjs web service... port=%s', thread_name, PORT)
    application = webapplication()
    application.listen(PORT)
    tornado.ioloop.IOLoop.current().start()

