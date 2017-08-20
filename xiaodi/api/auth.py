# coding=utf-8
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

import jwt
from tornado import gen
from xiaodi.api.errors import not_authorized_error
from xiaodi.api.mysql import User, Admin, BlackList, Permission, execute
from xiaodi.settings import SECRET_CODE
from xiaodi.settings import SU_ADMIN
from xiaodi.settings import SU_TOKEN
from xiaodi.settings import XIAODIER
from xiaodi.common.utils import gen_temp_object

LOG = logging.getLogger(__name__)


class AuthorizerHelper(object):
    @classmethod
    def generate_token(cls, user):
        return jwt.encode({
            "username": user.username,
            "exp": datetime.now() + timedelta(days=30)
        }, str(user.id) + SECRET_CODE)

    @classmethod
    def verify_token(cls, user, token):
        try:
            data = jwt.decode(token, str(user.id) + SECRET_CODE)
        except (jwt.ExpiredSignatureError, jwt.DecodeError, AttributeError):
            return False
        else:
            if data["username"] == user.username:
                return True
            else:
                return False


class Authorizer(object):
    @classmethod
    def get_instance(cls):
        return Authorizer()

    @gen.coroutine
    def _authenticate(self, object_=User, username=None, token=None):
        user = yield execute([('query', object_),
                              ('filter', object_.username == username),
                              ('first', None)])
        if user is None:
            raise gen.Return(not_authorized_error('wrong username'))
        if not AuthorizerHelper.verify_token(user, token):
            raise gen.Return(not_authorized_error('wrong token'))

        raise gen.Return(user)

    @gen.coroutine
    def authenticate_common(self, username=None, token=None):
        raise gen.Return((yield self._authenticate(username=username, token=token)))

    @gen.coroutine
    def authenticate_manager(self, username=None, token=None):
        raise gen.Return((yield self._authenticate(object_=Admin, username=username, token=token)))

    def authenticate_admin(self, username=None, token=None):
        if not (username == SU_ADMIN and token == SU_TOKEN):
            return not_authorized_error('wrong admin username or token')
        return gen_temp_object(username=username, token=token)

authorizer = Authorizer.get_instance()


def require_auth(permission, identified=False, innocence=False, xiaodier=False):
    def decorator(func):
        @wraps(func)
        @gen.coroutine
        def wrapper(self, *args, **kwargs):
            username = self.get_argument("username", None)
            token = self.get_argument("token", None)
            if permission == Permission.COMMON:
                self._G.user = yield authorizer.authenticate_common(
                    username=username, token=token
                )
            elif permission == Permission.MANAGER:
                self._G.user = yield authorizer.authenticate_manager(
                    username=username, token=token
                )
            elif permission == Permission.ADMIN:
                self._G.user = authorizer.authenticate_admin(
                    username=username, token=token
                )
            if identified and not self._G.user.identified:
                not_authorized_error('user %s is not identified' % self._G.user.nickname)
            if innocence:
                black_list = yield execute([('query', BlackList),
                                           ('filter', None),
                                           ('first', None)])
                if self._G.user.id in json.loads(black_list.list):
                    not_authorized_error('user %s is not innocence' % self._G.user.nickname)
            if xiaodier and self._G.user.role not in XIAODIER:
                not_authorized_error('user %s is not xiaodier' % self._G.user.nickname)
            # run generator until finish
            f = func(self, *args, **kwargs)
            while True:
                try:
                    f.send((yield next(f, None)))
                except StopIteration:
                    break
            raise gen.Return(None)
        return wrapper
    return decorator


