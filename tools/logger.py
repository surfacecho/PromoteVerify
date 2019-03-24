#!/usr/bin/env python
# coding=utf-8


import sys
import threading
import logging
import logging.config
import logging.handlers
import os
import traceback


logger = None


class Logger(object):
    __singleton_lock = threading.Lock()

    @staticmethod
    def getlogger(level=logging.DEBUG, name="log", path=''):
        global logger

        if not logger:
            with Logger.__singleton_lock:
                if not logger:
                    logger = Logger.setlogger(level, name, path)

        return logger

    @staticmethod
    def setlogger(level, name, path):
        try:
            logger = logging.getLogger(name)
            logger.setLevel(level)

            if not path:
                path = os.path.join(os.path.dirname(os.getcwd()), 'log')

            if not os.path.exists(path):
                os.makedirs(path)

            if not logger.handlers:
                console_handler = logging.StreamHandler()
                time_handler = logging.handlers.TimedRotatingFileHandler(os.path.join(path, '%s.log' % name),
                                                                         when="H", interval=12, encoding="utf-8")
                time_handler.suffix = "%Y-%m-%d_%H%M%S"
                formatter = logging.Formatter("%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s")

                console_handler.setFormatter(formatter)
                time_handler.setFormatter(formatter)

                logger.addHandler(console_handler)
                logger.addHandler(time_handler)

            return logger
        except Exception as e:
            print 'Init logger error!!! Well be exit -1!\n%s' % traceback.format_exc()
            sys.exit(-1)


if __name__ == '__main__':
    pass
    # log = Logger.getlogger()
    # log1 = Logger.getlogger()
    # print id(log), log
    # print id(log1), log1
    # log.info('OK')
    # log1.info('OK2')
