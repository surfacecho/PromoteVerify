#!/usr/bin/env python
# coding=utf-8


import threading
import traceback
import logging

import tornado.web
from tornado.ioloop import IOLoop
from tornado.web import asynchronous


from tools import threadpool
from phantomjsservice.config import LOG_NAME, NUM_THREADPOOL


threadPool = threadpool.ThreadPool(NUM_THREADPOOL)
logger = logging.getLogger(LOG_NAME)


class BaseHandler(tornado.web.RequestHandler):
    @asynchronous
    def get(self):
        # self.dojob('HTTP-GET')
        threadPool.add_task(self.dojob, 'HTTP-GET')  # tornado 4.5.2

    @asynchronous
    def post(self):
        # self.dojob('HTTP-POST')
        threadPool.add_task(self.dojob, 'HTTP-POST')  # tornado 4.5.2

    def writeAndFinish(self, content):
        try:
            self.write(content)
            self.finish()
        except Exception as e:
            logger.exception('Thread: %s, dojob exception, catch for avoiding thread crash.\n%s',
                             threading.currentThread().name, traceback.format_exc())

    def dojob(self, http_method):
        try:
            status, result = self.onRequest()
            IOLoop.instance().add_callback(self.writeAndFinish, result)
        except Exception as e:
            logger.error('Thread: %s, phantomjs web service has exception:\n%s',
                         threading.currentThread().name, traceback.format_exc())
            self.write_error(500)

    def onRequest(self):
        pass