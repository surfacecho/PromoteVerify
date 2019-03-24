#!/usr/bin/env python
# coding=utf-8


PORT = 9300

NUM_THREADPOOL = 50
NUM_PHANTOMJS_POOL = 10
NUM_PROXY_IP = 15

IN_COMING = 0

MAIN_PROCESS_PID = ''
JS_PID = []

LOG_PATH = ''
LOG_NAME = 'phantomjssrv'

STATUS_OK = 1
STATUS_ERROR = 0


def get_jspool():
    return NUM_PHANTOMJS_POOL


def set_jspool(num):
    global NUM_PHANTOMJS_POOL
    NUM_PHANTOMJS_POOL = num


def get_proxy_ip():
    return NUM_PROXY_IP


def set_proxy_ip(num):
    global NUM_PROXY_IP
    NUM_PROXY_IP = num


def get_incoming():
    return IN_COMING


def set_incoming(incoming):
    global IN_COMING
    IN_COMING = incoming


def get_pid():
    return MAIN_PROCESS_PID, JS_PID


def set_pid(main, js):
    global MAIN_PROCESS_PID, JS_PID
    MAIN_PROCESS_PID = main
    JS_PID = js


def supply_pid(pid):
    global JS_PID
    if pid not in JS_PID:
        JS_PID.append(pid)
