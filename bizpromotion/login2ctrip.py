#!/usr/bin/env python
# coding=utf-8


import traceback
import time
import threading
import requests
import json
import urllib

from requests.cookies import RequestsCookieJar

from tools.common import warning_title_loginctrip, warning_text_loginctrip
from tools.logger import Logger
from tools.netproxy import Proxy
from tools.warning import WarningMsg


class Login2Ctrip(object):

    __singleton_lock = threading.Lock()
    proxy = {'url': 'http://proxy.my.com/proxy',
             'params': {"method": "c_hotel", "group": "cadsl", "mode": 1, "url": 1, "level": "HTTPS", "expire": -1}
             }

    def __init__(self, *args, **kwargs):
        super(Login2Ctrip, self).__init__()
        self.logger = Logger.getlogger()
        self.url_userValidateNoRisk = 'https://passport.ctrip.com/gateway/api/soa2/12559/userValidateNoRisk'
        self.url_getMemberTaskByUID = 'https://passport.ctrip.com/gateway/api/soa2/11464/getMemberTaskByUID'
        self.url_userLogin = 'https://passport.ctrip.com/gateway/api/soa2/12559/userLogin'
        self.url_ssoCrossSetCookie = 'https://accounts.ctrip.com/ssoproxy/ssoCrossSetCookie'
        self.login_result = {}
        self.rmsToken = "fp=yt8oak-1bn7wi6-1g3pebz&vid=mytime.2rsmg9&pageId=10320670296&r=f3106a5833fb490b96920fc0c610ecb3&ip=myip&kpData=0_0_0&kpControl=0_0_0-0_0_0&kpEmp=0_0_0_0_0_0_0_0_0_0-0_0_0_0_0_0_0_0_0_0-0_0_0_0_0_0_0_0_0_0&screen=1280x800&tz= 8&blang=en-US&oslang=en-US&ua=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36&d=passport.ctrip.com&v=22"
        self.rmsTokenSearch = ''

        self.session = requests.Session()
        Proxy.get_proxy(self.session, Login2Ctrip.proxy, 10)
        self.logger.info('Get proxy: %s', self.session.proxies)
        self.ip = str(self.session.proxies['http'].split('@')[1].split(':')[0])
        self.port = str(self.session.proxies['http'].split('@')[1].split(':')[1])

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_singleton_login'):
            with cls.__singleton_lock:
                if not hasattr(cls, '_singleton_login'):
                    cls._singleton_login = super(Login2Ctrip, cls).__new__(cls)

        return cls._singleton_login

    def get_homePage(self):
        self.session.headers = {'Host': 'passport.ctrip.com',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                # 'Pragma': 'no-cache',
                                # 'Cache-Control': 'no-cache',
                                'Accept-Language':'en-US,en;q=0.5',
                                'Accept-Encoding':'gzip, deflate, br',
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                                # 'DNT': '1',
                                'Connection': 'keep-alive',
                                'Upgrade-Insecure-Requests': '1'
                                }

        flag = False
        url = r'https://passport.ctrip.com/user/login?BackUrl=http%3A%2F%2Fwww.ctrip.com%2F#ctm_ref=c_ph_login_buttom'

        try:
            self.logger.info("Prepare to open ctrip page for get cookies...")
            self.session.cookies = RequestsCookieJar()
            response = self.session.get(url=url, verify=False, timeout=10)
            if response.status_code == 200:
                flag = True
                self.logger.info("Open Ctrip Page:'%s'", url)
        except Exception as e:
            self.logger.error("Open Ctrip Page:'%s' failed.\n%s", url, traceback.format_exc())

        return flag

    def post_userValidateNoRisk(self):
        self.session.headers = {'Host': 'passport.ctrip.com',
                                'Accept': 'application/json, text/javascript, */*; q=0.01',
                                'X-Requested-With': 'XMLHttpRequest',
                                'contentType': 'application/json; charset=utf-8',
                                'Accept-Language': 'en-us',
                                'Accept-Encoding': 'gzip, deflate',
                                'Content-Type': 'application/json; charset=UTF-8',
                                'Origin': 'https://passport.ctrip.com',
                                'Content-Length': '',
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                                'Referer': 'https://passport.ctrip.com/user/login',
                                'DNT': '1',
                                'Connection': 'keep-alive'
                                }

        body = {"AccountHead": {"Platform": "P", "Extension": {}},
                "Data": {"accessCode": "7434E3DDCFF0EDA8", "strategyCode": "698D04A841768C87",
                         "userName": "JOIA817AJ98772NBQW72", "certificateCode": "someone",
                         "extendedProperties": [{"key": "LoginName", "value": "JOIA817AJ98772NBQW72"},
                                                {"key": "Platform", "value": "P"},
                                                {"key": "PageId", "value": "10320670296"},
                                                {"key": "rmsToken", "value": self.rmsToken},
                                                {"key": "URL", "value": "https://passport.ctrip.com/user/login"},
                                                {"key": "http_referer", "value": ""}]}}

        flag = False
        uid = ''
        token = ''
        RequestId = ''
        try:
            data = json.dumps(body)
            data = data.replace('mytime', str(int(time.time() * 1000)))
            data = data.replace('myip', self.ip)
            print data
            self.session.headers['Content-Length'] = str(len(data))
            response = self.session.post(url=self.url_userValidateNoRisk, data=data, verify=False)
            if response.status_code == 200:
                content = json.loads(response.content)
                if content['ReturnCode'] == 0 and u'成功' in content['Message']:
                    flag = True
                    result = json.loads(content['Result'])
                    # print 'returnCode:', result['returnCode']
                    # print 'message:', result['message']
                    uid = result['uid']
                    # print 'uid:', result['uid']
                    token = result['token']
                    # print 'token:', result['token']
                    # print 'expirationTime:', result['expirationTime']
                    # print 'ResponseStatus:', result['ResponseStatus']
                    RequestId = content['RequestId']
                    # print 'RequestId:', content['RequestId']
                    # print content
                    self.login_result = {'uid': uid, 'token': token, 'requestId': RequestId}
                    self.logger.info('Post: %s success!', self.url_userValidateNoRisk)
                else:
                    WarningMsg.sent(warning_title_loginctrip, warning_text_loginctrip % 'post:userValidateNoRisk failed!')
        except Exception as e:
            self.logger.error('Post: %s failed!\n%s', self.url_userValidateNoRisk, traceback.format_exc())

        return flag

    def post_getMemberTaskByUID(self):
        body = {"AccountHead": {"Extension": {"Token": self.login_result['token'], "TokenType": "uid_validate"}},
                "Data": {"sceneType": "S000", "platform": "ONLINE"}
                }

        flag = False
        try:
            data = json.dumps(body)
            self.session.headers['Content-Length'] = str(len(data))
            response = self.session.post(url=self.url_getMemberTaskByUID, data=data, verify=False)
            if response.status_code == 200:
                content = json.loads(response.content)
                if content['ReturnCode'] == 0 and u'成功' in content['Message']:
                    flag = True
                    self.login_result['requestId'] = content['RequestId']
                    self.logger.info('Post: %s success!', self.url_getMemberTaskByUID)
                else:
                    WarningMsg.sent(warning_title_loginctrip, warning_text_loginctrip % 'post:getMemberTaskByUID failed!')
        except Exception as e:
            self.logger.error('Post: %s failed!\n%s', self.url_getMemberTaskByUID, traceback.format_exc())

        return flag

    def post_userLogin(self):
        body = {"Data": {"accessCode": "010E3LOPCFF0EMA1", "strategyCode": "901FSD469FDO9WP7", "loginName": "",
                         "certificateCode": self.login_result['token'],
                         "extendedProperties": [{"key": "Platform", "value": "P"},
                                                {"key": "PageId", "value": "10320670296"},
                                                {"key": "rmsToken", "value": self.rmsToken},
                                                {"key": "URL", "value": "https://passport.ctrip.com/user/login"},
                                                {"key": "http_referer", "value": ""}]}}
        flag = False
        try:
            data = json.dumps(body)
            data = data.replace('mytime', str(int(time.time() * 1000)))
            data = data.replace('myip', self.ip)
            copydata = json.loads(data)
            self.rmsTokenSearch = filter(lambda x: x['key'] == 'rmsToken', copydata['Data']['extendedProperties'])[0]['value']
            self.session.headers['Content-Length'] = str(len(data))
            response = self.session.post(url=self.url_userLogin, data=data, verify=False)
            if response.status_code == 200:
                content = json.loads(response.content)
                if content['ReturnCode'] == 0 and u'成功' in content['Message']:
                    flag = True
                    self.login_result['ticket'] = json.loads(content['Result'])['ticket']
                    self.login_result['requestId'] = content['RequestId']
                    self.logger.info('Post: %s success!', self.url_userLogin)
                else:
                    WarningMsg.sent(warning_title_loginctrip, warning_text_loginctrip % 'post:userLogin failed!')
        except Exception as e:
            self.logger.error('Post: %s failed!\n%s', self.url_userLogin, traceback.format_exc())

        return flag

    def post_ssoCrossSetCookie(self):
        self.session.headers = {'Host': 'accounts.ctrip.com',
                                'Accept': 'application/json, text/javascript, */*; q=0.01',
                                'Accept-Language': 'en-us',
                                'Accept-Encoding': 'gzip, deflate',
                                'Content-Type': 'application/x-www-form-urlencoded',
                                'Origin': 'https://passport.ctrip.com',
                                'Content-Length': '',
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                                'Referer': 'https://passport.ctrip.com/user/login',
                                'DNT': '1',
                                'Connection': 'keep-alive'
                                }
        flag = False
        try:
            body = {"domain": "ctrip.com", "cticket": self.login_result['ticket'], "Secretkey": "17464605FFCC13881CA414A470966570"}
            body = urllib.urlencode(body)
            self.session.headers['Content-Length'] = str(len(body))
            response = self.session.post(url=self.url_ssoCrossSetCookie, data=body, verify=False)
            if response.status_code == 200:
                content = json.loads(response.content)
                if content['returnCode'] == 0 and 'success' in content['message'].lower():
                    flag = True
                    self.logger.info('Post: %s success!', self.url_ssoCrossSetCookie)
                else:
                    WarningMsg.sent(warning_title_loginctrip, warning_text_loginctrip % 'post:ssoCrossSetCookie failed!')
        except Exception as e:
            self.logger.error('Post: %s failed!\n%s', self.url_ssoCrossSetCookie, traceback.format_exc())

        return flag

    def view_personal_page(self):
        self.session.headers = {'Host': 'my.ctrip.com',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                'Pragma': 'no-cache',
                                'Cache-Control': 'no-cache',
                                'Accept-Language': 'en-us',
                                'Accept-Encoding': 'gzip, deflate',
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
                                'DNT': '1',
                                'Connection': 'keep-alive',
                                'Upgrade-Insecure-Requests': '1'
                                }
        flag = False
        url = 'http://my.ctrip.com/home/myinfo.aspx'
        try:
            response = self.session.get(url=url)
            if response.status_code == 200 and response.content:
                flag = True
                print response.content
        except Exception as e:
            print e

        return flag

    def login(self, relogin=False):
        flag = False
        try:
            if relogin:
                Proxy.get_proxy(self.session, Login2Ctrip.proxy, 10)
                self.logger.info('Get proxy: %s', self.session.proxies)
                self.ip = str(self.session.proxies['http'].split('@')[1].split(':')[0])
                self.port = str(self.session.proxies['http'].split('@')[1].split(':')[1])

            flag = self.get_homePage()
            if flag:
                flag = self.post_userValidateNoRisk()
                if flag:
                    flag = self.post_getMemberTaskByUID()
                    if flag:
                        flag = self.post_userLogin()
                        if flag:
                            flag = self.post_ssoCrossSetCookie()
        except Exception as e:
            self.logger.error('In method login() has exception:\n%s', traceback.format_exc())

        return (flag, self.session) if flag else (flag, None)


if __name__ == '__main__':
    login2ctrip = Login2Ctrip()
    login2ctrip.login()