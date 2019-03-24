#!/usr/bin/env python
# coding=utf-8


import cPickle
import threading
import logging
import time
import json

from requests.cookies import RequestsCookieJar
import requests
import traceback
import random

from phantomjsservice.base import BaseHandler
from phantomjsservice.phantomjspool import PhantomJSPool
from sessions import PROXY_LIST, HEADERS
from phantomjsservice.config import STATUS_OK, STATUS_ERROR, LOG_NAME, get_incoming, set_incoming

IN_COMING = 0
logger = logging.getLogger(LOG_NAME)
COOKIES = None


class PhantomJSHandler(BaseHandler):
    _thread_lock = threading.Lock()

    def onRequest(self):
        thread_name = threading.currentThread().name
        try:
            body = json.loads(self.request.body)
            hotelid = body['hotelid']
            checkin = body['checkin']
            checkout = body['checkout']
            is_mainland = body.get('ismainland', False)

            session = cPickle.loads(body['session'].encode('utf-8'))
            session.headers = HEADERS
            session.headers['Referer'] = 'http://hotels.ctrip.com/international/%s.html' % hotelid

            str_cookies = """IntlVID=110106-dd6d031f-adf7-4bb3-b573-6e3865dc6ee9; IntlVH=714698=NzE0Njk4; ASP.NET_SessionSvc=MTAuMTQuMy4xMjh8OTA5MHxvdXlhbmd8ZGVmYXVsdHwxNTM1MDIwMTg0MjE1; _abtest_userid=ce4103a9-d45a-46fb-8b99-7f7989cc1d61; IntlIOI=F; IntHotelCityID=splitsplitsplit{cin}split{cout}splitsplitsplit1split1split1; _bfa=1.1535354373678.48jpuz.1.1535354373678.1535354373678.1.2; _bfs=1.2; _RF1=114.248.121.31; _RSG=Xi4yDeSjiFF5PZWlfS9nFB; _RDG=289cac001ff9352104238dc57d7665f862; _RGUID=f3ecb5ca-0df0-4b21-b3f1-25ca6f823645; __zpspc=9.1.1535354375.1535354375.1%234%7C%7C%7C%7C%7C%23; _jzqco=%7C%7C%7C%7C1535354376067%7C1.1391924605.{time1}.{time2}.{time3}.{time4}.{time5}.undefined.0.0.1.1; MKT_Pagesource=PC; appFloatCnt=1; _bfi=p1%3D102104%26p2%3D0%26v1%3D1%26v2%3D0; _ga=GA1.2.331898612.1535354381; _gid=GA1.2.707995595.1535354381; manualclose=1"""
            timespam = int(time.time() * 1000)
            str_cookies = str_cookies.format(cin=checkin, cout=checkout, time1=timespam, time2=timespam, time3=timespam, time4=timespam, time5=timespam)

            cookies = RequestsCookieJar()
            for line in str_cookies.split(';'):
                name, value = line.strip().split('=', 1)
                cookies.set(name, value)

            session.cookies = cookies

            driver, retry, ex = None, 3, ''
            while not driver and retry > 0:
                driver, ex = PhantomJSPool.getphantomjs()
                if not driver:
                    retry -= 1
                    logger.info('Thread: %s, get driver is none, queue_phantomjs=%s.\n%s',
                                thread_name, PhantomJSPool.QUEUE_PHANTOMJS.qsize(), ex)
                    time.sleep(3)
                    continue
                else:
                    break

            if not driver:
                return STATUS_ERROR, {'Status': 0, 'Msg': 'Get driver failed!', 'eleven': '', 'session': '', 'reason': 'no phantomjs'}

            tslist = [30, 50, 60, 80]
            ts = timespam + random.sample(tslist, 1)[0]

            status, text, funname = PhantomJSPool.geteleven(session, driver['driver'], ts, is_mainland)
            PhantomJSPool.putphantomjs(driver)
            if status == 'failed':
                logger.info('Thread: %s, get eleven failed, ctrip hotel %s, [%s,%s).', thread_name, hotelid, checkin, checkout)
                return STATUS_ERROR, {'Status': 0, 'Msg': 'Get eleven failed!', 'eleven': '', 'session': '', 'reason': text}
            else:
                return STATUS_OK, {'Status': 1, 'Msg': 'Success!', 'eleven': text, 'funname': funname, 'ts': ts, 'session': cPickle.dumps(session), 'reason': ''}
        except Exception as e:
            logger.error('Thread: %s, PhantomJSHandler.onRequest() has some exception:\n%s', thread_name, traceback.format_exc())
            return {'Status': 0, 'Msg': 'Get eleven failed!', 'eleven': '', 'session': '', 'reason': e.message}


class StopServiceHandler(BaseHandler):
    def onRequest(self):
        pass
