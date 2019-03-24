#!/usr/bin/env python
# coding=utf-8


import commands
import re
import requests
import time
import threading
import traceback
import logging

from Queue import Queue
from phantomjsservice.config import LOG_NAME
from selenium import webdriver


logger = logging.getLogger(LOG_NAME)


class PhantomJSPool(object):
    """
    Package Selenium.webdriver.PhantomJSPool
    """

    _th_lock = threading.Lock()

    LIST_PHANTOMJS = list()
    QUEUE_PHANTOMJS = None

    IS_RENEW = False

    @staticmethod
    def init(*args, **kwargs):
        js_pid = []
        PhantomJSPool.QUEUE_PHANTOMJS = Queue(kwargs['num'])
        for i in xrange(kwargs['num']):
            service_args = []
            service_args.append('--load-images=false')
            service_args.append('--disk-cache=false')
            service_args.append('--ignore-ssl-errors=true')
            driver = webdriver.PhantomJS(service_args=service_args)
            driver.set_window_size(0, 0)
            pid = str(driver.service.process.pid)
            PhantomJSPool.QUEUE_PHANTOMJS.put({'pid': pid, 'driver': driver})
            js_pid.append(pid)
            logger.info('Thread: %s, create PhantomJS(PID=%s) and append to QUEUE_PHANTOMJS.', threading.currentThread().name, pid)

        return js_pid

    @staticmethod
    def getphantomjs():
        with PhantomJSPool._th_lock:
            try:
                if PhantomJSPool.QUEUE_PHANTOMJS.empty():
                    return None, ''
                else:
                    return PhantomJSPool.QUEUE_PHANTOMJS.get(), ''
            except Exception as e:
                return None, traceback.format_exc()

    @staticmethod
    def putphantomjs(driver):
        try:
            while 1:
                if PhantomJSPool.QUEUE_PHANTOMJS.full():
                    time.sleep(0.2)
                    continue
                else:
                    try:
                        driver.delete_all_cookies()
                        PhantomJSPool.QUEUE_PHANTOMJS.put(driver)
                        break
                    except:
                        PhantomJSPool.QUEUE_PHANTOMJS.put(driver)
                        break
        except:
            pass

    @staticmethod
    def generateMixed(driver, is_mainland):
        if is_mainland:
            digit = '19'
        else:
            digit = '17'

        content = '''var generateMixed = function (n) {
                   var chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                       'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'];
                   var res = '';

                   for (var i = 0; i < n; i++) {
                       var id = Math.ceil(Math.random() * 51);
                       res += chars[id];
                   }

                   return res;
               };
           return generateMixed(%s);\n
           ''' % digit

        return str(driver.execute_script(content))

    @staticmethod
    def geteleven(session, driver, ts, is_mainland, timeout=(6, 6)):
        reason = ''
        retry = 6
        eleven, funname = '', ''
        while retry > 0:
            eleven = ''
            content = ''
            rawarray = ''
            rawjs = ''

            funname = PhantomJSPool.generateMixed(driver, is_mainland)

            url = 'http://hotels.ctrip.com/international/Tool/cas-ocanball.aspx?callback=%s&_=%d' % (funname, ts)
            try:
                content = session.get(url, timeout=timeout).content
            except requests.Timeout as et:
                reason = 'Timeout'
                print 'Timeout:', et
                break
            except requests.ConnectionError as ec:
                reason = 'ConnectionError'
                print 'ConnectionError:', ec
                break
            except Exception as ex:
                reason = 'program exception'
                print 'Exception:', ex
                break

            rawarray = content[content.find('([') + 1:content.find('],function') + 1]
            number = re.findall('String.fromCharCode\(item-(\d*)\)', content)
            
            if not number:
                retry -= 1
                continue

            decodejs = '''var rawarray = %s; 
                    return rawarray.map(function(item) 
                    {return String.fromCharCode(item - %s)}).join('')
                    ''' % (rawarray, number[0])

            rawjs = driver.execute_script(decodejs)
            rawjs = str(rawjs.replace('\r', ''))

            if rawjs.find('fake') > 0:
                retry -= 1
                continue

            if rawjs.find('http://hotels.ctrip.com') > 0:
                retry -= 1
                continue

            rawjs = re.sub('(/international/.*?\.html)', '', rawjs)

            content = funname + ' = function (data){window.eleven = data()};\n' + rawjs + '; return window.eleven;'
            eleven = driver.execute_script(content)

            del content
            del rawarray
            del rawjs

            break
        else:
            eleven, funname, reason = '', '', 'other'

        return ('success', eleven, funname) if eleven else ('failed', reason, funname)
