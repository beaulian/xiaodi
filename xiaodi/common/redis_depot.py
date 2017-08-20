# coding=utf-8
import logging
from tornado import gen
from cached_property import cached_property
from xiaodi.settings import REDIS_REWARD_DB, REDIS_TASK_DB
from xiaodi.settings import AUTO_DELETE_QUEUE, AUTO_FINISH_QUEUE
from xiaodi.common.redis_client import get_aredis_client, call, get_redis_client
from xiaodi.common.utils import gen_random_str
from xiaodi.common.safeeval import safe_eval

LOG = logging.getLogger(__name__)


class InvalidRewardError(Exception):
    pass


def default_key_func(*args):
    if not args:
        return gen_random_str(6)
    elif len(args) == 1:
        return str(args[0])

    return '_'.join([str(arg) for arg in args])


class _BaseAsyncDepot(object):
    def __init__(self, db=0, key_func=default_key_func):
        self._aclient = get_aredis_client(db)
        self._key_func = key_func


class _RewardUtils(object):
    @classmethod
    def split_reward(cls, user, reward):
        if user.original_point < reward:
            bright_point = reward - user.original_point
            original_point = user.original_point
        else:
            bright_point = 0
            original_point = reward

        return [bright_point, original_point]


class _SyncRewardDepotMixin(object):
    @staticmethod
    def __key_func(*args):
        return default_key_func(*args)

    @cached_property
    def __client(self):
        return get_redis_client(REDIS_REWARD_DB)

    def set_reward(self, user, reward, *args):
        self.__client.hset(user.id, self.__key_func(*args),
                           _RewardUtils.split_reward(user, reward))

    def get_reward(self, user, *args):
        return safe_eval(self.__client.hget(user.id, self.__key_func(*args)))

    def exist_reward(self, user, *args):
        return self.__client.hexists(user.id, self.__key_func(*args))

    def del_reward(self, user, *args):
        self.__client.hdel(user.id, self.__key_func(*args))


class _RewardDepot(_BaseAsyncDepot, _SyncRewardDepotMixin):

    @gen.coroutine
    def aset_reward(self, user, reward, *args):
        raise gen.Return((yield call(self._aclient.hset, user.id, self._key_func(*args),
                                     _RewardUtils.split_reward(user, reward))))

    @gen.coroutine
    def aget_reward(self, user, *args):
        reward_list = yield call(self._aclient.hget, user.id, self._key_func(*args))

        raise gen.Return(safe_eval(reward_list))

    @gen.coroutine
    def adel_reward(self, user, *args):
        yield call(self._aclient.hdel, user.id, self._key_func(*args))

    @gen.coroutine
    def aexist_reward(self, user, *args):
        exist = yield call(self._aclient.hexists, user.id, self._key_func(*args))

        raise gen.Return(exist)

    @gen.coroutine
    def aget_all_rewards(self, user):
        all_rewards = yield call(self._aclient.hvals, user.id)
        raise gen.Return(sum([sum(safe_eval(reward))
                              for reward in all_rewards]
                             ))

    @gen.coroutine
    def aget_all_reward_by(self, user, bright_point=False):
        index = 0 if bright_point else 1
        all_rewards = yield call(self._aclient.hvals, user.id)

        raise gen.Return(sum([sum(safe_eval(reward)[index])
                              for reward in all_rewards]
                             ))

    @gen.coroutine
    def aget_available_reward(self, user):
        available = (user.original_point + user.bright_point) - \
                    (yield self.aget_all_rewards(user))
        if available < 0:
            LOG.error('user %s has invalid reward number: %d' % (user.id, available))
            raise InvalidRewardError('user %s has invalid reward number: %d' % (user.id, available))

        raise gen.Return(available)

    @gen.coroutine
    def adeduct_reward(self, user, *args):
        reward = yield self.aget_reward(user, *args)
        user.bright_point -= reward[0]
        user.original_point -= reward[1]
        if user.bright_point < 0 or user.original_point < 0:
            raise InvalidRewardError('user %s has invalid point: (%d, %d)' %
                                     (user.id, user.bright_point, user.original_point))
        yield self.adel_reward(user, *args)


class _SyncTaskDepotMixin(object):
    @staticmethod
    def __key_func(*args):
        return default_key_func(*args)

    @property
    def __client(self):
        return get_redis_client(REDIS_TASK_DB)

    def __add_task(self, key, value, queue=None):
        self.__client.zadd(queue, key, value)

    def __del_task(self, key, queue=None):
        self.__client.zrem(queue, key)

    def __scan_task(self, queue=None):
        return self.__client.zscan_iter(queue)

    def del_delete_task(self, *args):
        self.__del_task(self.__key_func(*args), queue=AUTO_DELETE_QUEUE)

    def del_finish_task(self, *args):
        self.__del_task(self.__key_func(*args), queue=AUTO_FINISH_QUEUE)

    def scan_delete_task(self):
        return self.__scan_task(queue=AUTO_DELETE_QUEUE)

    def scan_finish_task(self):
        return self.__scan_task(queue=AUTO_FINISH_QUEUE)


class _TaskDepot(_BaseAsyncDepot, _SyncTaskDepotMixin):
    @gen.coroutine
    def _aadd_task(self, key, value, queue=None):
        yield call(self._aclient.zadd, queue, key, value)

    @gen.coroutine
    def _adel_task(self, key, queue=None):
        yield call(self._aclient.zrem, queue, key)

    @gen.coroutine
    def _ascan_task(self, queue=None):
        result = yield call(self._aclient.zscan, queue)
        raise gen.Return(result)

    @gen.coroutine
    def aadd_delete_task(self, time, *args):
        raise gen.Return((yield self._aadd_task(self._key_func(*args), time, queue=AUTO_DELETE_QUEUE)))

    @gen.coroutine
    def aadd_finish_task(self, time, *args):
        raise gen.Return((yield self._aadd_task(self._key_func(*args), time, queue=AUTO_FINISH_QUEUE)))

    @gen.coroutine
    def adel_delete_task(self, *args):
        raise gen.Return((yield self._adel_task(self._key_func(*args), queue=AUTO_DELETE_QUEUE)))

    @gen.coroutine
    def adel_finish_task(self, *args):
        raise gen.Return((yield self._adel_task(self._key_func(*args), queue=AUTO_FINISH_QUEUE)))

    @gen.coroutine
    def ascan_delete_task(self):
        raise gen.Return((yield self._ascan_task(AUTO_DELETE_QUEUE)))

    @gen.coroutine
    def ascan_finish_task(self):
        raise gen.Return((yield self._ascan_task(AUTO_FINISH_QUEUE)))

RewardDepot = _RewardDepot(db=REDIS_REWARD_DB)
TaskDepot = _TaskDepot(db=REDIS_TASK_DB)
