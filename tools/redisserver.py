#!/usr/bin/env python
# coding=utf-8


import threading
import redis
import traceback

from settings.settings import Settings
from warning import WarningMsg
from common import warning_title_redis, warning_text_redis, \
    warning_title_rediscluster, warning_text_rediscluster


def operator_status(func):
    def gen_status(*args, **kwargs):
        result, error = '', ''
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            error = str.format("redis:{0}", str(e))
        return {"result": result, "error":  error}

    return gen_status


class RedisServer(object):
    __th_lock = threading.Lock()

    @staticmethod
    def connect():
        try:
            if not hasattr(RedisServer, '_connect_pool'):
                RedisServer.__create_pool()

            return redis.Redis(connection_pool=RedisServer._connect_pool)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

    @staticmethod
    def __create_pool():
        cnf = Settings.get()['redisserver']
        RedisServer._connect_pool = redis.ConnectionPool(host=cnf['host'],
                                                         port=cnf['port'],
                                                         db=cnf['db'],
                                                         password=cnf['pwd'])

    @staticmethod
    def get(name):
        try:
            redis_cli = RedisServer.connect()
            value = redis_cli.get(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return value

    @staticmethod
    def set(name, value):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.set(name, value)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def hget(name, key):
        try:
            redis_cli = RedisServer.connect()
            value = redis_cli.hget(name, key)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return value

    @staticmethod
    def hgetall(name):
        try:
            redis_cli = RedisServer.connect()
            value = redis_cli.hgetall(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return value

    @staticmethod
    def hset(name, key, value):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.hset(name, key, value)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def hdel(name, key):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.hdel(name, key)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def incr(name):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.incr(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def rename(src, dst):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.rename(src, dst)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def delete(name):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.delete(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def exists(name):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.exists(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def llen(name):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.llen(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def lpop(name):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.lpop(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def rpop(name):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.rpop(name)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status

    @staticmethod
    def ltrim(name, start, end):
        try:
            redis_cli = RedisServer.connect()
            status = redis_cli.lrange(name, start, end)
            redis_cli.ltrim(name, end+1, -1)
        except Exception as e:
            WarningMsg.sent(warning_title_redis, warning_text_redis % repr(e))
            raise e

        return status


class RedisClusterServer(object):
    __th_lock = threading.Lock()

    @staticmethod
    def connect():
        try:
            if not hasattr(RedisClusterServer, '_cluster_connect_pool'):
                RedisClusterServer.__create_pool()

            return redis.Redis(connection_pool=RedisClusterServer._cluster_connect_pool)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

    @staticmethod
    def __create_pool():
        cnf = Settings.get()['rediscluster']
        RedisClusterServer._cluster_connect_pool = redis.ConnectionPool(host=cnf['host'],
                                                                        port=cnf['port'],
                                                                        password=cnf['pwd'])

    @staticmethod
    def get(name):
        try:
            redis_cli = RedisClusterServer.connect()
            value = redis_cli.get(name)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return value

    @staticmethod
    def set(name, value):
        try:
            redis_cli = RedisClusterServer.connect()
            status = redis_cli.set(name, value)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return status

    @staticmethod
    def hget(name, key):
        try:
            redis_cli = RedisClusterServer.connect()
            value = redis_cli.hget(name, key)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return value

    @staticmethod
    def hgetall(name):
        try:
            redis_cli = RedisClusterServer.connect()
            value = redis_cli.hgetall(name)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return value

    @staticmethod
    def hset(name, key, value):
        try:
            redis_cli = RedisClusterServer.connect()
            status = redis_cli.hset(name, key, value)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return status

    @staticmethod
    def incr(name):
        try:
            redis_cli = RedisClusterServer.connect()
            status = redis_cli.incr(name)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return status

    @staticmethod
    def rename(src, dst):
        try:
            redis_cli = RedisClusterServer.connect()
            status = redis_cli.rename(src, dst)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return status

    @staticmethod
    def delete(name):
        try:
            redis_cli = RedisClusterServer.connect()
            status = redis_cli.delete(name)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return status

    @staticmethod
    def exists(name):
        try:
            redis_cli = RedisClusterServer.connect()
            status = redis_cli.exists(name)
        except Exception as e:
            WarningMsg.sent(warning_title_rediscluster, warning_text_rediscluster % repr(e))
            raise e

        return status


if __name__ == '__main__':
    try:
        status = RedisServer.hset('test', 'a', '1-1-2-1')
        status1 = RedisServer.hdel('test', 'kko')
        print status,status1
    except Exception as e:
        print e

