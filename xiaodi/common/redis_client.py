# coding=utf-8

import tornadoredis
from tornado import gen
from xiaodi.settings import REDIS_HOST
from xiaodi.settings import REDIS_PORT
from xiaodi.settings import REDIS_PASSWORD
from xiaodi.common.cache import Cache

base_kwargs = {
    'host': REDIS_HOST,
    'port': REDIS_PORT,
    'password': REDIS_PASSWORD
}


@Cache.cache_in_request(async=False)
def get_aredis_client(db):

    redis_kwargs = dict({
        'selected_db': db,
        'connection_pool': tornadoredis.ConnectionPool(wait_for_available=True)
    }, **base_kwargs)

    client = tornadoredis.Client(**redis_kwargs)
    client.connect()

    return client


@Cache.cache_in_request(async=False)
def get_redis_client(db):
    from redis import StrictRedis

    redis_kwargs = dict({
        'db': db,
    }, **base_kwargs)

    return StrictRedis(**redis_kwargs)


@Cache.cache_in_request(async=False)
@gen.coroutine
def call(func, *args):
    result = yield gen.Task(func, *args)

    raise gen.Return(result)
