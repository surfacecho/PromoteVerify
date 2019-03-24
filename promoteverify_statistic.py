#!/usr/bin/env python
# coding=utf-8


import commands
import logging
import os
import traceback

import time
import sys

from settings.settings import Settings
from tools.logger import Logger
from tools.mysqlserver import MysqlServer

logger = None


def statistic(last_hour, statisitc_path, statisitc_fname):
    """
    statistic
    :param last_hour:
    :param statisitc_path:
    :param statisitc_fname:
    :return:
    """
    try:
        logger.info('starting statistic count of last hour: %s ...', last_hour)
        cmd = "cat %s/%s | grep '%s' | grep 'status_code=' | grep -v 'ERROR' | wc -l" % (statisitc_path, statisitc_fname, last_hour)
        status, total_text = commands.getstatusoutput(cmd)
        if status == 0:
            logger.info('statistic total count=%s, cmd=%s', total_text, cmd)
            cmd = "cat %s/%s | grep '%s' | grep 'result = 1' | wc -l" % (statisitc_path, statisitc_fname, last_hour)
            status, success_text = commands.getstatusoutput(cmd)
            if status == 0:
                logger.info('statistic success count=%s, cmd=%s', success_text, cmd)
                sql_insert = """insert into table(statisticdate,success,total,createtime)
                values('%s',%s,%s,NOW()) on duplicate key update success=values(success), total=values(total);"""
                sql_insert = sql_insert % (last_hour, success_text, total_text)
                success, status = MysqlServer.insert(sql_insert)
                if success:
                    logger.info('completed statistic count of last hour: %s ...', last_hour)
                else:
                    logger.info('sql: %s', sql_insert)
                    logger.error('insert into failed:\n%s', status)
    except Exception as e:
        logger.error('statistic has some error:\n%s', traceback.format_exc())


if __name__ == '__main__':
    app_startup_path = os.path.dirname(os.path.realpath(__file__))
    params = sys.argv[1:]
    assert 'environment' in params[0], "Must be contains the name 'environment' at first argv for launching..."
    environment = params[0].split('=')[1].strip(' ')
    settings = Settings.get(app_startup_path, environment)

    if len(sys.argv) - 1 < 1:
        print 'Please give some params for service launching... such as [python app.py db_use=master last_hour=2018-07-23_10 statisitc_path= statisitc_fname= log_path=/usr/local/log]'
        sys.exit(-1)

    last_hour = ''
    statisitc_path = ''
    statisitc_fname = ''
    log_path = ''
    for p in params[1:]:
        name = p.split('=')[0].strip(' ')
        if name == 'db_use':
            settings['db_use'] = p.split('=')[1].strip(' ')
        elif name == 'last_hour':
            last_hour = p.split('=')[1].replace('_', ' ')
        elif name == 'statisitc_path':
            statisitc_path = p.split('=')[1].strip(' ')
        elif name == 'statisitc_fname':
            statisitc_fname = p.split('=')[1].strip(' ')
        elif name == 'log_path':
            log_path = p.split('=')[1].strip(' ')

    logger = Logger.getlogger(level=logging.DEBUG, name='promoteverify_statistic', path=log_path)
    logger.info('<<<========================= Promoteverify click statistic This log starting at %s =========================>>>', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

    logger.info('last_hour = %s', last_hour)
    logger.info('statisitc_path = %s', statisitc_path)
    logger.info('statisitc_path = %s', statisitc_path)

    statistic(last_hour, statisitc_path, statisitc_fname)

