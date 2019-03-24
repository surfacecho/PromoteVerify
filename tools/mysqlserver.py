#!/usr/bin/env python
# coding=utf-8


import time
import torndb
import traceback
import threading

from settings.settings import Settings
from warning import WarningMsg
from common import warning_title_mysql, warning_text_mysql
# from tornado.options import define, options

_th_lock = threading.Lock()


class MysqlServer(object):
    cnf = {}

    @staticmethod
    def connect():
        if not MysqlServer.cnf:
            settings = Settings.get()
            if settings['db_use'] == 'master':
                MysqlServer.cnf = settings['mysqlserver_master']
            elif settings['db_use'] == 'slave':
                MysqlServer.cnf = settings['mysqlserver_slave']

        return torndb.Connection(host='%s:%s' % (MysqlServer.cnf['host'], MysqlServer.cnf['port']),
                                 database=MysqlServer.cnf['db'],
                                 user=MysqlServer.cnf['user'],
                                 password=MysqlServer.cnf['pwd'])

    @staticmethod
    def execute(sql, retry=3):
        success = 0
        status = []
        while retry:
            try:
                mysql_cli = MysqlServer.connect()
                status = mysql_cli.execute(sql)
                success = 1
                status = 1
                break
            except Exception as e:
                retry -= 1
                if retry > 0:
                    time.sleep(10)
                    continue
                else:
                    status = traceback.format_exc()
                    WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
                    break

        return success, status

    @staticmethod
    def query(sql, retry=3):
        success = 0
        status = []
        while retry:
            try:
                mysql_cli = MysqlServer.connect()
                status = mysql_cli.query(sql)
                success = 1
                break
            except Exception as e:
                retry -= 1
                if retry > 0:
                    time.sleep(10)
                    continue
                else:
                    status = traceback.format_exc()
                    WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
                    break

        return success, status

    @staticmethod
    def get(sql, retry=3):
        success = 0
        status = []
        while retry:
            try:
                mysql_cli = MysqlServer.connect()
                status = mysql_cli.get(sql)
                success = 1
                break
            except Exception as e:
                retry -= 1
                if retry > 0:
                    time.sleep(10)
                    continue
                else:
                    status = traceback.format_exc()
                    WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
                    break

        return success, status

    @staticmethod
    def insertmany(sql, data, retry=3):
        with _th_lock:
            success = 0
            status = 0
            while retry:
                try:
                    mysql_cli = MysqlServer.connect()
                    status = mysql_cli.insertmany(sql, data)
                    success = 1
                    break
                except Exception as e:
                    retry -= 1
                    if retry > 0:
                        time.sleep(10)
                        continue
                    else:
                        status = traceback.format_exc()
                        WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
                        break

            return success, status

    @staticmethod
    def insert(sql, retry=3):
        with _th_lock:
            success = 0
            status = 0
            while retry:
                try:
                    mysql_cli = MysqlServer.connect()
                    status = mysql_cli.insert(sql)
                    success = 1
                    break
                except Exception as e:
                    retry -= 1
                    if retry > 0:
                        time.sleep(10)
                        continue
                    else:
                        status = traceback.format_exc()
                        WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
                        break

            return success, status

    @staticmethod
    def updatemany(sql, data, retry=3):
        with _th_lock:
            success = 0
            status = 0
            while retry:
                try:
                    mysql_cli = MysqlServer.connect()
                    status = mysql_cli.updatemany(sql, data)
                    success = 1
                    break
                except Exception as e:
                    retry -= 1
                    if retry > 0:
                        time.sleep(10)
                        continue
                    else:
                        status = traceback.format_exc()
                        WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
                        break

            return success, status

    @staticmethod
    def update(sql, retry=3):
        with _th_lock:
            success = 0
            status = 0
            while retry:
                try:
                    mysql_cli = MysqlServer.connect()
                    status = mysql_cli.update(sql)
                    success = 1
                    break
                except torndb.IntegrityError as ie:
                    print ie
                    success = 0
                    status = ie
                    break
                except Exception as e:
                    retry -= 1
                    if retry > 0:
                        time.sleep(10)
                        continue
                    else:
                        status = traceback.format_exc()
                        WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
                        break

            return success, status

