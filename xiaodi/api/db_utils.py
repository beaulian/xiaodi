# coding=utf-8
import json
from tornado import gen
from sqlalchemy import and_
from xiaodi.api.errors import invalid_argument_error
from xiaodi.api.errors import internal_server_error
from xiaodi.api.mysql import execute, PointRecord, Award, Engagement


@gen.coroutine
def get_db_object_by_attr(object_, **kwargs):
    assert len(kwargs) >= 1, 'function get_db_object_by_attr need argument'

    if 'ignore' in kwargs:
        ignore = kwargs.pop('ignore')
    else:
        ignore = False
    if len(kwargs) > 1:
        filter_ = and_(*[getattr(object_, key) == value
                         for key, value in kwargs.iteritems()])
    else:
        key, value = kwargs.popitem()
        filter_ = getattr(object_, key) == value
    user = yield execute(sqls=[('query', object_),
                               ('filter', filter_),
                               ('first', None)])
    if not user and not ignore:
        raise gen.Return(invalid_argument_error('wrong %s' % key))

    raise gen.Return(user)


@gen.coroutine
def first_award(user, key):
    type_, type_doc, point = key
    award = yield get_db_object_by_attr(Award, user_id=user.id, type=type_, ignore=True)
    if award is None:
        user.original_point += point
        point_record = PointRecord(
            user_id=user.id,
            type=type_doc,
            balance=user.bright_point + user.original_point,
            number='+' + str(point)
        )
        award = Award(user_id=user.id, type=type_)
        yield execute(('add_all', [user, award, point_record]))
        yield execute(('commit', None))


@gen.coroutine
def add_engagement(user, key):
    type_, engagement = key
    en = yield get_db_object_by_attr(Engagement, user_id=user.id, ignore=True)
    if en is None:
        raise gen.Return(internal_server_error('user %s loss engagement info' % user.id))
    list_ = json.loads(en.engagement)
    list_[-1] += engagement
    en.engagement = json.dumps(list_)
    yield execute(('add', en))
    yield execute(('commit', None))
