#!/usr/bin/env python
# coding=utf-8


import os
import time
import traceback
import threading
import MySQLdb
from MySQLdb import cursors

from settings.settings import Settings
from warning import WarningMsg
from common import warning_title_mysql, warning_text_mysql


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

        return MySQLdb.connect(host=MysqlServer.cnf['host'],
                               port=int(MysqlServer.cnf['port']),
                               db=MysqlServer.cnf['db'],
                               user=MysqlServer.cnf['user'],
                               passwd=MysqlServer.cnf['pwd'],
                               cursorclass=cursors.DictCursor,
                               charset='utf8')

    @staticmethod
    def fetchone(query, args=None):
        success, status, db, cursor = 0, None, None, None

        try:
            db = MysqlServer.connect()
            cursor = db.cursor()
            status = cursor.execute(query=query, args=args)
            status = cursor.fetchone()
            success = 1
        except Exception as e:
            status = traceback.format_exc()
            WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

        return success, status

    @staticmethod
    def fetchmany(query, args=None, size=1):
        success, status, db, cursor = 0, None, None, None

        try:
            db = MysqlServer.connect()
            cursor = db.cursor()
            status = cursor.execute(query=query, args=args)
            status = cursor.fetchmany(size=size)
            success = 1
        except Exception as e:
            status = traceback.format_exc()
            WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

        return success, status

    @staticmethod
    def fetchall(query, args=None):
        success, status, db, cursor = 0, None, None, None

        try:
            db = MysqlServer.connect()
            cursor = db.cursor()
            status = cursor.execute(query=query, args=args)
            status = cursor.fetchall()
            success = 1
        except Exception as e:
            status = traceback.format_exc()
            WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

        return success, status

    @staticmethod
    def execute(query, args=None):
        success, status, db, cursor = 0, None, None, None

        try:
            db = MysqlServer.connect()
            cursor = db.cursor()
            status = cursor.execute(query=query, args=args)
            db.commit()
            success = 1
        except Exception as e:
            if db:
                db.rollback()
            status = traceback.format_exc()
            WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

        return success, status

    @staticmethod
    def executemany(query, args=None):
        success, status, db, cursor = 0, None, None, None

        try:
            db = MysqlServer.connect()
            cursor = db.cursor()
            status = cursor.executemany(query=query, args=args)
            db.commit()
            success = 1
        except Exception as e:
            if db:
                db.rollback()
            status = traceback.format_exc()
            WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

        return success, status

    @staticmethod
    def transactions(groups):
        success, status, db, cursor = 0, None, None, None

        try:
            db = MysqlServer.connect()
            cursor = db.cursor()
            flag = 0
            for query in groups:
                if query[0] and query[1]:
                    status = cursor.executemany(query=query[0], args=query[1])
                    flag += 1

            if flag > 0:
                db.commit()

            success = 1
        except Exception as e:
            if db:
                db.rollback()
            status = traceback.format_exc()
            WarningMsg.sent(warning_title_mysql, warning_text_mysql % repr(e))
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

        return success, status


if __name__ == '__main__':
    pass
