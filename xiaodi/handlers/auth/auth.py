# coding=utf-8
import json
import random
import hashlib

from tornado import gen
from datetime import datetime
from xiaodi.api.mysql import User, Admin, PointRecord, Auth, Engagement, Sign, RequestRecord
from xiaodi.api.mysql import execute, Permission
from xiaodi.api.db_utils import get_db_object_by_attr
from xiaodi.api.errors import not_authorized_error
from xiaodi.api.errors import invalid_argument_error
from xiaodi.api.errors import already_exist_error
from xiaodi.common.image_handler import save_image_to_oss
from xiaodi.settings import OSS_HEADIMG_PATH
from xiaodi.settings import INVITE_AWARD_POINT
from xiaodi.settings import DEFAULT_POINT
from xiaodi.settings import DEFAULT_HEADIMG
from xiaodi.settings import DEFAULT_CREDIBILITY
from xiaodi.common.tasks import TaskNames
from xiaodi.common.tasks import CommonTaskFactory
from xiaodi.common.password_manager import password_manager


@gen.coroutine
def login_authentication(phone, password):
    user = yield get_db_object_by_attr(User, phone=phone)
    if user is None:
        raise gen.Return(not_authorized_error('wrong phone'))
    if not password_manager.verify_password(password, user.password):
        raise gen.Return(not_authorized_error('wrong password'))

    raise gen.Return(user)


@gen.coroutine
def manager_login_authentication(username, password):
    user = yield get_db_object_by_attr(Admin, username=username)
    if user is None:
        raise gen.Return(not_authorized_error('wrong username'))
    if not password_manager.verify_password(password, user.password):
        raise gen.Return(not_authorized_error('wrong password'))

    raise gen.Return(user)


def generate_identifier(username):
    username_list = username.split("-")
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
        temp = yield get_db_object_by_attr(User, code=code, ignore=True)
        if not temp:
            break
        code = "".join(random.sample(random_seed, random.randint(4, 8)))

    raise gen.Return(code)


@gen.coroutine
def register_user(password=None, nickname=None, code=None,
                  headimg=None, sex=None, phone=None, unique_id=None):
    if (yield get_db_object_by_attr(User, phone=phone, ignore=True)) is not None:
        raise gen.Return(already_exist_error('phone %s alreay exist' % phone))
    if (yield get_db_object_by_attr(User, nickname=nickname, ignore=True)) is not None:
        raise gen.Return(already_exist_error('nickname %s alreay exist' % nickname))
    if headimg:
        headimg_path = yield save_image_to_oss(headimg, OSS_HEADIMG_PATH,
                                         str(datetime.now()), when_fail=DEFAULT_HEADIMG)
    else:
        headimg_path = DEFAULT_HEADIMG

    bright_point = 0
    if code:
        user = yield get_db_object_by_attr(User, code=code)
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
        password=password_manager.encrypt(password),
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


@gen.coroutine
def identify_user(user, role=None, school='cqu', sid=None,
                  password=None, truename=None):
    if user.identified:
        raise gen.Return(already_exist_error('user %s is already identified' % user.nickname))

    if (yield get_db_object_by_attr(Auth, school_id=sid, ignore=True)) is not None:
        raise gen.Return(already_exist_error('school_id %s is already identified' % sid))

    result = yield CommonTaskFactory.get_task(TaskNames.IDENTIFY_USER.value).run(
        school=school, sid=sid, password=password, truename=truename
    )
    if result is None:
        raise gen.Return(invalid_argument_error('certification is failed, please check the params'))

    auth = Auth(
        user_id=user.id,
        truename=truename,
        school_id=sid,
        school_role=role,
        identifier=""
    )
    engagement = Engagement(
        user_id=user.id,
        engagement=json.dumps([0])
    )
    sign = Sign(
        user_id=user.id,
        day=-1,
        record=json.dumps([])
    )
    user.identified = True
    user.school = school

    yield execute(('add_all', [auth, engagement, sign, user]))
    yield execute(('commit', None))

    raise gen.Return(None)


@gen.coroutine
def fulltime_request(user, address=None):
    auth = yield get_db_object_by_attr(Auth, user_id=user.id, ignore=True)
    if auth and auth.identifier:
        raise gen.Return(already_exist_error('user %s is already a xiaodier' % user.nickname))

    request_record = RequestRecord(user_id=user.id, detail=address)

    yield execute(('add', request_record))
    yield execute(('commit', None))

    raise gen.Return(None)
