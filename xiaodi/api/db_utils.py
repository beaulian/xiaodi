# coding=utf-8

from tornado import gen
from xiaodi.api.errors import invalid_argument_error
from xiaodi.api.mysql import db, execute
from xiaodi.api.mysql import User


@gen.coroutine
def get_db_object_by_attr(object_, **kwargs):
    assert 1 <= len(kwargs) <= 2, 'pass wrong argument to function get_db_object_by_attr'

    if len(kwargs) == 2 and 'ignore' in kwargs:
        ignore = kwargs.pop('ignore')
    else:
        ignore = False
    key, value = kwargs.popitem()
    user = yield execute([('query', object_),
                          ('filter', getattr(object_, key) == value),
                          ('first', None)])
    if not user and not ignore:
        raise gen.Return(invalid_argument_error('wrong %s' % key))

    raise gen.Return(user)
