# coding=utf-8
import logging
from tornado import gen
from datetime import datetime
from xiaodi.api.mysql import Auth, User
from xiaodi.api.mysql import execute
from xiaodi.api.db_utils import get_db_object_by_attr
from xiaodi.api.errors import internal_server_error
from xiaodi.api.errors import invalid_argument_error
from xiaodi.api.errors import already_exist_error
from xiaodi.common.image_handler import remove_image_from_oss
from xiaodi.common.image_handler import save_image_to_oss
from xiaodi.common.const import FULLTIME_ROLE
from xiaodi.settings import DEFAULT_HEADIMG
from xiaodi.settings import OSS_HEADIMG_PATH
from xiaodi.common.password_manager import password_manager
from xiaodi.common.password_manager import WrongOldPasswordError

LOG = logging.getLogger(__name__)


@gen.coroutine
def get_user(user):
    user_ = user.to_json()
    if user.role in FULLTIME_ROLE:
        auth = yield get_db_object_by_attr(Auth, user_id=user.id, ignore=True)
        if not auth:
            raise gen.Return(internal_server_error('fulltime user was not identified'))
        user_['identifier'] = auth.identifier

    raise gen.Return(user_)


@gen.coroutine
def put_user(user, nickname=None, headimg=None, sex=None, introduction=None):
    if nickname and nickname != user.nickname:
        if (yield get_db_object_by_attr(User, nickname=nickname, ignore=True)) is not None:
            raise gen.Return(already_exist_error('nickname %s is already existed' % nickname))
        user.nickname = nickname
    if headimg:
        if user.headimg != DEFAULT_HEADIMG:
            result = yield remove_image_from_oss(user.headimg)
            if not result:
                LOG.error('failed to remove image: %s' % user.headimg)

        headimg_path = yield save_image_to_oss(headimg, OSS_HEADIMG_PATH,
                                               str(datetime.now()), when_fail=DEFAULT_HEADIMG)
        user.headimg = headimg_path
    if sex:
        user.sex = sex
    if introduction:
        user.introduction = introduction

    yield execute(('add', user))
    yield execute(('commit', None))


@gen.coroutine
def do_change_password(user, old=None, new=None):
    try:
        user_ = password_manager.change_password(user, old, new)
    except WrongOldPasswordError:
        raise gen.Return(invalid_argument_error('wrong old password'))
    else:
        yield execute(('add', user_))
        yield execute(('commit', None))


@gen.coroutine
def do_forget_password(phone=None, password=None):
    user = yield get_db_object_by_attr(User, phone=phone)
    user = password_manager.forget_password(user, password)

    yield execute(('add', user))
    yield execute(('commit', None))
