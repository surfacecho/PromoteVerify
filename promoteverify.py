#!/usr/bin/env python
# coding=utf-8


import logging
import traceback
import time
import datetime
import os
import sys
import json
import random

from Queue import Queue
from bizpromotion.login2ctrip import Login2Ctrip
from bizpromotion.clickbooking import CtripClickBooking
from settings.settings import Settings
from tools.common import warning_title_clickbooking, warning_text_clickbooking, warning_title_clickbooking_stic, \
    warning_text_clickbooking_stic
from tools.redisserver import RedisServer
from tools.logger import Logger
from tools.warning import WarningMsg


if __name__ == '__main__':
    try:
        if len(sys.argv) - 1 > 0:
            app_startup_path = os.path.dirname(os.path.realpath(__file__))
            params = sys.argv[1:]
            assert 'environment' in params[0], "Must be contains the name 'environment' at first argv for launching..."
            environment = params[0].split('=')[1].strip(' ')
            settings = Settings.get(app_startup_path, environment)
            settings['redisserver']['db'] = ''

            for p in params[1:]:
                name = p.split('=')[0].strip(' ')
                if name == 'log_path':
                    settings['log_path'] = p.split('=')[1].strip(' ')
                elif name == 'js_url':
                    settings['js_url'] = p.split('=')[1].strip(' ')
        else:
            print 'Please give some args like:environment=dev log_path=/source/python/... for launching application! Well be exit 0!'
            sys.exit(0)
    except Exception as e:
        print 'Application init settings error!!! Well be exit -1!\n%s' % traceback.format_exc()
        sys.exit(-1)

    logger = Logger.getlogger(level=logging.DEBUG, name='promoteverify', path=settings['log_path'])
    logger.info('<<<========================= Promote Verify This log starting at %s =========================>>>', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    logger.info("Application launched environment is: '%s'!", environment)

    # session
    session = None

    # Redis Key:
    task_key = 'PromoteVerify'
    task_status_key = 'PromoteVerify_Status'

    while 1:
        try:
            login2ctrip = Login2Ctrip()
        except Exception as e:
            logger.error('Create Login2Ctrip object error!\n%s', traceback.format_exc())
            time.sleep(60)
            continue

        flag, session = login2ctrip.login()
        if not flag:
            time.sleep(60)
            continue
        else:
            break

    while 1:
        try:
            clicker = CtripClickBooking(session, settings['js_url'], login2ctrip)
            break
        except Exception as e:
            logger.error('Create CtripClickBooking object error!\n%s', traceback.format_exc())
            time.sleep(60)
            continue

    totalClick = 0

    last_visit_time = None
    hour = 3600 * 2

    while 1:
        try:
            if not RedisServer.exists(task_key):
                # logger.info('Not found the redis key: %s !', task_key)
                time.sleep(15)
                if last_visit_time:
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    time_diff = (datetime.datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S') -
                                 datetime.datetime.strptime(last_visit_time, '%Y-%m-%d %H:%M:%S')).seconds
                    if time_diff >= hour:
                        logger.warning('Found that after the last:%s click task, to now redis key: %s did not click the task, over %s hours, please check soon...',
                                       last_visit_time, task_key, time_diff/3600)
                        msg = 'Found that after the last:%s click task, to now redis key: %s did not click the task, over %s hours, please check soon...' % (last_visit_time, time_diff/3600, task_key)
                        WarningMsg.sent(warning_title_clickbooking, warning_text_clickbooking % msg)
                        time.sleep(60 * 10)

                continue

            redis_task = RedisServer.lpop(task_key)
            if not redis_task:
                logger.info('Found the redis key: %s of task values is None!', task_key)
                time.sleep(10)
                continue
            else:
                last_visit_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                logger.info('The last time of visit redis is %s.', last_visit_time)

            RedisServer.set(task_status_key, 1)
            redis_task = json.loads(redis_task)
            # ------------ use for testing ------------
            # redis_task = {"totalClick":10,
            #               "subHotelList":[
            #                   {"subHotelID":"5448782","checkIn":"2018-07-12","checkOut":"2018-07-13"},
            #                   {"subHotelID":"7238317","checkIn":"2018-06-18","checkOut":"2018-06-19"}
            #               ]
            #               }
            # ------------ use for testing ------------
            totalClick = redis_task['totalClick']
            task_queue = Queue(len(redis_task['subHotelList']))
            logger.info('---------------Get a new redis task: totalClick=%s, task:---------------\n%s', redis_task['totalClick'], redis_task)

            random.shuffle(redis_task['subHotelList'])
            for t in redis_task['subHotelList']:
                t.update(subRoomList=[])
                task_queue.put(t)
            # map(lambda x: x.update(subRoomList=[]), redis_task['subHotelList'])
            # map(lambda x: task_queue.put(x), redis_task['subHotelList'])

            logger.info('task_queue size = %s', task_queue.qsize())

            warning_click = 0
            dic_statistic = {}
            while totalClick > 0 and not task_queue.empty():
                click_task = task_queue.get()
                logger.info('Get a task from task_queue: %s', click_task)
                logger.info('Current task_queue size = %s, remaining totalClick = %s', task_queue.qsize(), totalClick)
                if not click_task["subRoomList"]:
                    params_list = clicker.getbookingparams(click_task['subHotelID'], click_task['checkIn'], click_task['checkOut'])
                    click_task['subRoomList'] = params_list

                newlogin = False
                fix_count = len(click_task['subRoomList'])
                logger.info('hotel %s subRoomList=%s', click_task['subHotelID'], fix_count)
                if fix_count:
                    if fix_count > 2:
                        slice_task = random.sample(click_task['subRoomList'], 2)
                    else:
                        slice_task = click_task['subRoomList']

                    fix_count = len(slice_task)

                    for task in slice_task:
                        if totalClick <= 0:
                            break
                        result, newlogin = clicker.clickbooking(task)
                        if newlogin:
                            break

                        if result:
                            totalClick -= 1
                            if task['hotelid'] not in dic_statistic:
                                dic_statistic[task['hotelid']] = [{str(task['room']): 1, 'checkin': task['checkIn'], 'checkout': task['checkOut']}]
                            else:
                                value = dic_statistic[task['hotelid']]
                                room = filter(lambda x: str(task['room']) in x and task['checkIn'] == x['checkIn'] and task['checkOut'] == x['checkOut'], value)
                                if room:
                                    room[0][str(task['room'])] = room[0][str(task['room'])] + 1
                                else:
                                    dic_statistic[task['hotelid']].append({str(task['room']): 1, 'checkin': task['checkIn'], 'checkout': task['checkOut']})

                            fix_count -= 1
                            warning_click += 1

                            time.sleep(0.2)
                            continue
                        else:
                            break

                    if newlogin:
                        del click_task['subRoomList'][:]
                        task_queue.put(click_task)

                    # if fix_count == 0:
                    #     task_queue.put(click_task)

            RedisServer.set(task_status_key, 0)
            logger.info('Current task_queue size = %s, task totalClick = %s, remaining totalClick = %s', task_queue.qsize(), redis_task['totalClick'], totalClick)
            logger.info('Set redis key task_status_key=0')
            logger.info('Statistic: %s', json.dumps(dic_statistic))
            del task_queue

            logger.info('---------------This time redis task completed!---------------\n\n')
        except Exception as e:
            logger.error('Click booking program error!\n%s', traceback.format_exc())
            try:
                RedisServer.set(task_status_key, 0)
            except Exception as ex:
                logger.error('Set redis key task_status_key=0 error!\n%s', traceback.format_exc())
