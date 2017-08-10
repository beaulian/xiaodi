# coding=utf-8
import jwt
import pickle
import logging
from tornado import gen
from functools import wraps
from collections import namedtuple
from passlib.hash import md5_crypt
from datetime import datetime, timedelta

from xiaodi.settings import SU_ADMIN
from xiaodi.settings import SU_TOKEN
from xiaodi.settings import SECRET_CODE
from xiaodi.api.errors import not_authorized_error
from xiaodi.api.mysql import db, User, Admin, Permission, execute

LOG = logging.getLogger(__name__)


'''gen.Return 一旦coroutine装饰器捕获到了异常
   self._finished就会被置为True，并执行相应的
   return
'''


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

    @classmethod
    def encrypt(cls, password):
        return md5_crypt.encrypt(password)

    @classmethod
    def verify_password(cls, password, password_hash):
        if md5_crypt.verify(password, password_hash):
            return True
        else:
            return False


class Authorizer(object):
    def __init__(self):
        self.db = db

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
        raise gen.Return(self._authenticate(username=username, token=token))

    @gen.coroutine
    def authenticate_manager(self, username=None, token=None):
        raise gen.Return(self._authenticate(object_=Admin, username=username, token=token))

    def authenticate_admin(self, username=None, token=None):
        if not (username == SU_ADMIN and token == SU_TOKEN):
            return not_authorized_error('wrong admin username or token')
        return namedtuple('User', ['username', 'token'])(username, token)

authorizer = Authorizer.get_instance()


def require_auth(permission):
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



