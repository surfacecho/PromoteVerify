#!/usr/bin/env python
# coding=utf-8


import cPickle
import copy
import threading
import traceback

import time
import requests
import json
import urllib

from Queue import Queue

from tools.common import warning_title_clickbooking, warning_text_clickbooking
from tools.logger import Logger
from tools.netproxy import Proxy
from tools.phantomjspool import PhantomJSPool
from tools.redisserver import RedisServer
from tools.warning import WarningMsg


class CtripClickBooking(object):

    __singleton_lock = threading.Lock()

    def __init__(self, session, js_url, login2ctrip):
        super(CtripClickBooking, self).__init__()
        self.logger = Logger.getlogger()
        self.tasklist = 'PromoteVerify'
        self.proxy = {'url': 'http://proxy.my.com/proxy',
                      'params': {"method": "c_hotel", "group": "cadsl", "mode": 1, "url": 1, "level": "HTTPS", "expire": -1}
                      }
        self.js_url = js_url
        self.session = session
        self.login2ctrip = login2ctrip
        self.url_inputneworder = 'http://hotels.ctrip.com/internationalbook/inputneworder.aspx?ctm_ref=hi_0_0_0_0_lst_sr_1_df_ls_1_n_hi_bk_1_0'

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_singleton_click'):
            with cls.__singleton_lock:
                if not hasattr(cls, '_singleton_click'):
                    cls._singleton_click = super(CtripClickBooking, cls).__new__(cls)

        return cls._singleton_click

    def fixsessionproxy(self):
        while 1:
            try:
                Proxy.get_proxy(self.session, self.proxy, 5)
                break
            except Exception as e:
                self.logger.error('Get proxt error!\n%s', traceback.format_exc())
                time.sleep(3)
                continue

    def relogin(self, **kwargs):
        logined = False

        while not logined:
            logined, session = self.login2ctrip.login(relogin=True)
            if logined:
                self.session = session
                self.logger.info('Relogin success!!! Hotel=%s, room=%s, checkin=%s, checkout=%s',
                                 kwargs['hotelid'], kwargs['room'], kwargs['checkIn'], kwargs['checkOut'])
                return True
            else:
                logined = False
                self.logger.info('Relogin failed!!! retry... Hotel=%s, room=%s, checkin=%s, checkout=%s',
                                 kwargs['hotelid'], kwargs['room'], kwargs['checkIn'], kwargs['checkOut'])
                time.sleep(60)
                continue

    def getminprices(self, data):
        if len(data) > 1:
            if data[0]['totalprice'] < data[1]['totalprice']:
                return data[0]
            else:
                fix_data = self.fixprice(data)
                return fix_data
        else:
            data[0]['islowerprice'] = 1
            return data[0]

    def fixprice(self, data):
        price = data[0]['totalprice']
        fix_data = filter(lambda x: x['totalprice'] == price, data)
        fix_data.sort(key=lambda x: x['totalroomprice'])
        return fix_data[0]

    def loadsdata(self, raw_data):
        # (hotelid, dates, response.content)
        hotelid = raw_data[0]
        dates = raw_data[1]
        rawjson = json.loads(raw_data[2])
        process_result = []
        try:
            # parse json
            base_room_list = []
            sub_room_list = []
            hotel_room_data = rawjson['HotelRoomData']
            if hotel_room_data:
                if hotel_room_data['roomList'] and hotel_room_data['subRoomList']:
                    # base_room_list = map(lambda x: {'id': x['id'], 'name': x['name']}, hotel_room_data['roomList'])
                    sub_room_list = filter(lambda x: x['canBook'], hotel_room_data['subRoomList'])
                    sub_room_list = filter(lambda x: x['roomVendorID'] == -1, sub_room_list)
                    if sub_room_list:
                        for sub_room in sub_room_list:
                            if process_result:
                                fix = filter(lambda x: str(x['room']) == str(sub_room['id']), process_result)
                                if fix:
                                    continue

                            item = {}
                            # static params
                            item['roomNumber'] = '1'
                            item['RoomPerson'] = '2'
                            item['childnum'] = '1'
                            item['paymentterm'] ='PP'
                            item['amountCurrency'] = ''
                            item['lastStr'] = ''
                            item['isFirstCheckDiscount'] = 'false'
                            item['operationtype'] = 'NEWHOTELORDER'
                            item['cityName'] = ''
                            item['cityId'] = ''
                            item['city'] = ''
                            item['country'] = ''
                            item['FromBu'] = 'hotels.ctrip.com/overseadetail'
                            item['IsPkg'] = 'false'
                            item['channeltype'] = ''
                            item['defaultcoupon'] = ''

                            # dynamic params
                            item['room'] = sub_room['id']
                            item['checkAvalID'] = sub_room['checkAvlID'] if sub_room['checkAvlID'] is not None else sub_room['id']
                            item['roomRatesID'] = sub_room['ratePlanID'] if sub_room['ratePlanID'] is not None else ''
                            item['amountVal'] = str(int(sub_room['price'].get('TotalPrice', 0)))
                            item['priceCX'] = str(int(sub_room['price'].get('TotalPrice', 0)))
                            item['swid'] = sub_room['shadowid'] if sub_room['shadowid'] is not None else ''
                            item['sctx'] = sub_room['shadowCtx'] if sub_room['shadowCtx'] is not None else ''
                            item['resource'] = hotelid
                            item['hotelid'] = hotelid
                            item['hotel'] = hotelid
                            item['checkIn'] = dates['checkin']
                            item['checkOut'] = dates['checkout']
                            item['startdate'] = dates['checkin']
                            item['depdate'] = dates['checkout']
                            item['isLowestPrice'] = 'false'
                            item['rmsTokenSearch'] = self.login2ctrip.rmsTokenSearch
                            item['totalprice'] = sub_room['price'].get('TotalPrice', 0)
                            item['totalroomprice'] = sub_room['price'].get('TotalRoomPrice', 0)
                            process_result.append(item)

                        process_result.sort(key=lambda x: x['totalprice'])
                        self.getminprices(process_result)['isLowestPrice'] = 'true'
                        map(lambda x: x.__delitem__('totalprice'), process_result)
                        map(lambda x: x.__delitem__('totalroomprice'), process_result)

            del sub_room_list
            del base_room_list
            del hotel_room_data
            return process_result
        except Exception as e:
            self.logger.error('Hotel %s [%s,%s), parse json data error!\n%s', hotelid, dates['checkin'], dates['checkout'], traceback.format_exc())
            return []

    def get_eleven(self, hotelid, checkin, checkout, session):
        url = self.js_url
        eleven = 'failed'
        try:
            body = {'hotelid': hotelid, 'checkin': checkin, 'checkout': checkout, 'session': cPickle.dumps(session)}
            response = requests.Session().post(url, data=json.dumps(body))
            if response.status_code == 200 and response.text:
                text = json.loads(response.text)
                if text['Status'] == 1:
                    eleven = text['eleven']
                    session = cPickle.loads(text['session'].encode('utf-8'))
        except Exception as e:
            time.sleep(10)
            eleven, session = 'failed', session
            self.logger.error('Thread: %s, method get_eleven() has exception:\n%s', threading.currentThread().name, traceback.format_exc())

        return eleven, session

    def getbookingparams(self, hotel, checkin, checkout):
        eleven_ref = "http://hotels.ctrip.com/international/{sub_hotelid}.html"
        eleven_headers = {'Referer': '',
                          'Host': 'hotels.ctrip.com',
                          'Accept': '*/*',
                          'Accept-Encoding': 'gzip, deflate',
                          'Accept-Language': 'en-us',
                          'Connection': 'keep-alive',
                          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                          }

        price_ref = "http://hotels.ctrip.com/international/{sub_hotelid}.html?checkin={checkin}&checkout={checkout}&fixsubhotel=T"
        url_price = "http://hotels.ctrip.com/international/Tool/AjaxHotelRoomInfoDetailPart.aspx?City=73&Hotel={sub_hotelid}&EDM=F&Pkg=F&ep=&StartDate={checkin}&DepDate={checkout}&RoomNum=1&RoomQuantity=1&UserUnicode=&requestTravelMoney=F&promotionid=&Coupons=&CCoupons=&PageLoad=false&t={timestamp}&childNum=1&FixSubHotel=T&allianceid=&sid=&eleven={eleven}"
        price_headers = {'Referer': '',
                         'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
                         'Host': 'hotels.ctrip.com',
                         'Pragma': 'no-cache',
                         'Accept': '*/*',
                         'Cache-Control': 'no-cache',
                         'Accept-Encoding': 'gzip, deflate',
                         'Accept-Language': 'en-us',
                         'DNT': '1',
                         'Connection': 'keep-alive',
                         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
                         }

        result_list = []
        while 1:
            try:
                eleven, session = self.get_eleven(hotel, checkin, checkout, self.session)
                if eleven == 'failed':
                    self.logger.info('Hotel %s get eleven failed! retry...', hotel)
                    self.fixsessionproxy()
                    continue

                self.logger.info('Hotel %s get eleven: %s', hotel, eleven)
                self.session.headers = price_headers
                self.session.headers['Referer'] = price_ref.format(sub_hotelid=hotel, checkin=checkin, checkout=checkout)
                url = url_price.format(sub_hotelid=hotel, checkin=checkin, checkout=checkout, timestamp=int(time.time() * 1000), eleven=eleven)
                # req_start = time.time()
                response = self.session.get(url, timeout=20)
                # req_cost = time.time() - req_start
                if response.status_code == 200:
                    if response.content and response.content.rfind('"ResultCode":1') > -1:
                        params_list = self.loadsdata((hotel, {'checkin': checkin, 'checkout': checkout}, response.content))
                        result_list.extend(params_list)
                    else:
                        self.logger.info('Request price hotel %s, [%s, %s), content invalid.', hotel, checkin, checkout)
                    break
                else:
                    continue
            except requests.Timeout as et:
                self.logger.error('Request price hotel %s, [%s, %s), timeout, retry...', hotel, checkin, checkout)
                self.fixsessionproxy()
            except requests.ConnectionError as ec:
                self.logger.error('Request price hotel %s, [%s, %s), connection error, retry...', hotel, checkin, checkout)
                self.fixsessionproxy()
            except Exception as ex:
                self.logger.error('Request price hotel %s, [%s, %s), error, retry...\n%s', hotel, checkin, checkout, traceback.format_exc())
                self.fixsessionproxy()

        return result_list

    def clickbooking(self, task):
        flag, newlogin = False, False

        while not flag:
            if newlogin:
                break

            result = self.click(task)
            if result == 1:
                flag, newlogin = True, False
                break
            elif result == 2:
                self.fixsessionproxy()
                flag, newlogin = False, False
                continue
            elif result == 3:
                flag = False
                newlogin = self.relogin(hotelid=task['hotelid'], room=task['room'], checkIn=task['checkIn'], checkOut=task['checkOut'])
                break
            elif result == 4:
                flag, newlogin = False, False
                break
            elif result == 5:
                flag, newlogin = False, False
                continue

        return flag, newlogin

    def click(self, task):
        click_url = 'http://hotels.ctrip.com/internationalbook/inputneworder.aspx?ctm_ref=hi_0_0_0_0_lst_sr_1_df_ls_1_n_hi_bk_1_0'
        click_ref = "http://hotels.ctrip.com/international/{sub_hotelid}.html?checkin={checkin}&checkout={checkout}&fixsubhotel=T"
        click_headers = {'Content-Type': 'application/x-www-form-urlencoded',
                         'Origin': 'http://hotels.ctrip.com',
                         'Host': 'hotels.ctrip.com',
                         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                         'Pragma': 'no-cache',
                         'Cache-Control': 'no-cache',
                         'Accept-Encoding': 'gzip, deflate',
                         'Accept-Language': 'en-US',
                         'Connection': 'keep-alive',
                         'DNT': '1',
                         'Content-Length': '',
                         'Referer': click_ref,
                         'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                         'Upgrade-Insecure-Requests': '1'
                         }
        result = 0
        try:
            self.session.headers = click_headers
            self.session.headers['Referer'] = click_ref.format(sub_hotelid=task['hotelid'], checkin=task['checkIn'], checkout=task['checkOut'])
            body = urllib.urlencode(task)
            self.session.headers['Content-Length'] = str(len(body))
            try:
                response = self.session.post(url=click_url, data=body, timeout=30)
            except requests.Timeout as et:
                result = 2
                self.logger.error('Click abnormal! [result = 2], time out. retry...')
                return result
            except requests.ConnectionError as ec:
                result = 2
                self.logger.error('Click abnormal! [result = 2], connection error. retry...')
                return result
            except Exception as e:
                result = 2
                self.logger.error('Click abnormal! [result = 2], error. retry...\n%s', traceback.format_exc())
                return result

            html = ''
            html = response.text
            if u'订单填写页' in html:
                result = 1
                self.logger.info('Click success! [result = 1], status_code=%s, Hotel=%s, room=%s, checkin=%s, checkout=%s',
                                 response.status_code, task['hotelid'], task['room'], task['checkIn'], task['checkOut'])
            elif u'登录' in html or u'登录首页' in html \
                    or u'AutoSubmit()' in html \
                    or u'https://passport.ctrip.com/user/login' in html \
                    or u'502 Bad Gateway' in html \
                    or u'400 Bad Request' in html:
                result = 3
                self.logger.info('Click abnormal! [result = 3], status_code=%s, [Re-login] Hotel=%s, room=%s, checkin=%s, checkout=%s',
                                 response.status_code, task['hotelid'], task['room'], task['checkIn'], task['checkOut'])
                # self.logger.info('HTML:\n%s', html)
            elif u'出错页' in html or u'手慢了' in html:
                result = 4
                self.logger.info('Click abnormal! [result = 4], status_code=%s, [Verify-failed] Hotel=%s, room=%s, checkin=%s, checkout=%s',
                                 response.status_code, task['hotelid'], task['room'], task['checkIn'], task['checkOut'])
            else:
                result = 4
                self.logger.info('Click abnormal! [unknown html!], status_code=%s, Hotel=%s room=%s, checkin=%s, checkout=%s',
                                 response.status_code, task['hotelid'], task['room'], task['checkIn'], task['checkOut'])
                self.logger.info('Unknown html:\n%s', html)
                msg = u"status_code=%s, found the new html content, see the log!" % response.status_code
                WarningMsg.sent(warning_title_clickbooking, warning_text_clickbooking % msg)
        except Exception as e:
            result = 5
            self.logger.error(e)
            self.logger.error('Click program error! [result = 5], Hotel=%s, room=%s, checkin=%s, checkout=%s\n%s',
                              task['hotelid'], task['room'], task['checkIn'], task['checkOut'], traceback.format_exc())

        return result
