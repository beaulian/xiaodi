# coding=utf-8
import random
import hashlib

from tornado import gen
from datetime import datetime
from xiaodi.api.mysql import User, Admin, PointRecord
from xiaodi.api.mysql import execute, Permission
from xiaodi.api.auth import AuthorizerHelper
from xiaodi.api.errors import not_authorized_error
from xiaodi.api.errors import bad_request_error
from xiaodi.api.errors import invalid_argument_error
from xiaodi.api.errors import already_exist_error
from xiaodi.common.image_handler import allow_image_format
from xiaodi.common.image_handler import allow_image_size
from xiaodi.common.image_handler import save_image_to_oss
from xiaodi.settings import OSS_HEADIMG_PATH
from xiaodi.settings import INVITE_AWARD_POINT
from xiaodi.settings import DEFAULT_POINT
from xiaodi.settings import DEFAULT_HEADIMG
from xiaodi.settings import DEFAULT_CREDIBILITY


@gen.coroutine
def login_authentication(phone, password):
    user = yield execute([('query', User),
                          ('filter', User.phone == phone),
                          ('first', '')])
    if user is None:
        raise gen.Return(not_authorized_error('wrong phone'))
    if not AuthorizerHelper.verify_password(password, user.password):
        raise gen.Return(not_authorized_error('wrong password'))

    raise gen.Return(user)


@gen.coroutine
def manager_login_authentication(username, password):
    user = yield execute(sqls=[('query', Admin),
                              ('filter', Admin.username == username),
                              ('first', None)])
    if user is None:
        raise gen.Return(not_authorized_error('wrong username'))
    if not AuthorizerHelper.verify_password(password, user.password):
        raise gen.Return(not_authorized_error('wrong password'))

    raise gen.Return(user)


def generate_identifier(username):
    username_list = username.split("-")
    # 将username_list乱序
    random.shuffle(username_list)

    return hashlib.md5("-".join(username_list)).hexdigest()


def generate_unique_username():
    import uuid

    return str(uuid.uuid1())


@gen.coroutine
def generate_invitingcode():
    random_seed = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
        'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'z',
        'x', 'c', 'v', 'b', 'n', 'm', 'P', 'O', 'I', 'U',
        'Y', 'T', 'R', 'E', 'W', 'Q', 'A', 'S', 'D', 'F',
        'G', 'H', 'J', 'K', 'L', 'M', 'N', 'B', 'V', 'C',
        'X', 'Z'
    ]
    code = "".join(random.sample(random_seed, random.randint(4, 8)))
    while True:
        temp = yield execute([('query', User),
                              ('filter', User.code == code),
                              ('first', None)])
        if not temp:
            break
        code = "".join(random.sample(random_seed, random.randint(4, 8)))

    raise gen.Return(code)


@gen.coroutine
def register_user(password=None, nickname=None, code=None,
                  headimg=None, sex=None, phone=None, unique_id=None):
    if (not nickname) or (not phone) or (not password):
        raise gen.Return(bad_request_error('miss argument: nickname, phone, password are required'))
    if (yield execute([('query', User),
                       ('filter', User.phone == phone),
                       ('first', None)])) is not None:
        raise gen.Return(already_exist_error('phone %s alreay exist' % phone))
    if (yield execute([('query', User),
                       ('filter', User.nickname == nickname),
                       ('first', None)])) is not None:
        raise gen.Return(already_exist_error('nickname %s alreay exist' % nickname))
    if headimg:
        if not allow_image_format(headimg[0]["filename"]):
            raise gen.Return(invalid_argument_error('invalid image format: only jpg, ipeg, png is supported'))

        if not allow_image_size(headimg[0]):
            raise gen.Return(invalid_argument_error('invalid image size: less than or equal 2M is required'))

        headimg_path = save_image_to_oss(headimg[0], OSS_HEADIMG_PATH, str(datetime.now()))
    else:
        headimg_path = DEFAULT_HEADIMG

    bright_point = 0
    if code:
        user = yield execute([('query', User),
                              ('filter', User.code == code),
                              ('first', None)])
        if user:
            user.bright_point += INVITE_AWARD_POINT
            user.code = None
            execute(('add', user))

            point_record = PointRecord(
                username=user.username,
                type='邀好友注册',
                balance=user.bright_point + user.original_point,
                number='+%d' % INVITE_AWARD_POINT,
                time=datetime.now().__format__("%Y-%m-%d")
            )
            yield execute(('add', point_record))
            yield execute(('commit', None))
            bright_point = INVITE_AWARD_POINT

    user = User(
        username=generate_unique_username(),
        password=AuthorizerHelper.encrypt(password),
        nickname=nickname,
        phone=phone,
        role=Permission.COMMON,
        unique_id=unique_id,
        code=(yield generate_invitingcode()),
        headimg=headimg_path,
        sex=sex,
        identified=False,
        school="",
        campus="",
        hostel="",
        introduction="",
        original_point=DEFAULT_POINT,
        bright_point=bright_point,
        credibility=DEFAULT_CREDIBILITY
    )
    yield execute(('add', user))
    yield execute(('commit', None))

    raise gen.Return(user)
