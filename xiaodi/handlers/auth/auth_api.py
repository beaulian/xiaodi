# coding=utf-8
from tornado import gen
from tornado.web import asynchronous

from auth import login_authentication
from auth import manager_login_authentication
from auth import register_user
from xiaodi.api.abc import BaseApiHandler
from xiaodi.api.auth import require_auth
from xiaodi.api.auth import AuthorizerHelper
from xiaodi.api.mysql import Permission
from xiaodi.common.utils import xss_filter
from xiaodi.api.errors import HTTPAPIError
from tornado.ioloop import IOLoop


class LoginHandler(BaseApiHandler):
    def post(self):
        phone = self.get_argument("phone", None)
        password = self.get_argument("password", None)

        user = yield login_authentication(phone, password)

        self.async_write({
                "status": "success",
                "username": user.username,
                "token": AuthorizerHelper.generate_token(user)
        })

    @require_auth(Permission.COMMON)
    def put(self):
        self.async_write({
            "status": "success",
            "token": AuthorizerHelper.generate_token(self._G.user)
        })


class ManagerLoginHandler(BaseApiHandler):
    def post(self):
        username = self.get_argument("username", None)
        password = self.get_argument("password", None)

        user = yield manager_login_authentication(username=username, password=password)

        self.async_write({
                "status": "success",
                "username": user.username,
                "token": AuthorizerHelper.generate_token(user)
        })

    @require_auth(Permission.MANAGER)
    def put(self):
        self.async_write({
            "status": "success",
            "token": AuthorizerHelper.generate_token(self._G.user)
        })


class RegisterHandler(BaseApiHandler):
    @require_auth(Permission.ADMIN)
    def post(self):
        nickname = xss_filter(self.get_argument("nickname", None))
        phone = self.get_argument("phone", None)
        headimg = self.request.files.get("headimg", None)
        sex = self.get_argument("sex", "男")
        password = self.get_argument("password", None)
        unique_id = self.get_argument("unique_id", None)
        code = self.get_argument("code", None)

        user = yield register_user(password=password, nickname=nickname, code=code,
                                   headimg=headimg, sex=sex, phone=phone, unique_id=unique_id)

        self.async_write({
            "status": "success",
            "user": user.to_json(),
            "token": AuthorizerHelper.generate_token(user)
        })

