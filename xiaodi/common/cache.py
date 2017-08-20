# coding=utf-8
from functools import wraps
from tornado import gen


def hash_to_str(*args, **kwargs):
    return str(hash(str(args) + str(kwargs)))


# only query once for every request
class Cache(object):
    @classmethod
    def cache_in_request(cls, name=None, key_func=hash_to_str, async=True):
        def async_decorator(func):
            @wraps(func)
            @gen.coroutine
            def async_wrapper(*args, **kwargs):
                key = name if name else key_func(*args, **kwargs)
                key = func.__name__ + key
                if not cls.exist_request_cache(key):
                    result = yield func(*args, **kwargs)
                    cls.set_request_cache(key, result)
                raise gen.Return(cls.get_request_cache(key))
            return async_wrapper

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = name if name else key_func(*args, **kwargs)
                key = func.__name__ + key
                if not cls.exist_request_cache(key):
                    result = func(*args, **kwargs)
                    cls.set_request_cache(key, result)
                return cls.get_request_cache(key)
            return wrapper

        if async:
            return async_decorator
        else:
            return decorator

    @classmethod
    def _clean_request_cache(cls, key):
        delattr(cls, key)

    @classmethod
    def _cache_key(cls, key):
        prefix = 'cache'
        return '%s:%s' % (prefix, key)

    @classmethod
    def get_request_cache(cls, key):
        key = cls._cache_key(key)
        return getattr(cls, key)

    @classmethod
    def set_request_cache(cls, key, o):
        key = cls._cache_key(key)
        setattr(cls, key, o)

    @classmethod
    def exist_request_cache(cls, key):
        key = cls._cache_key(key)
        return hasattr(cls, key)