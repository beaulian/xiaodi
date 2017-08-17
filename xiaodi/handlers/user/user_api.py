# coding=utf-8

from user import get_user
from user import put_user
from user import do_change_password
from user import do_forget_password
from xiaodi.api.abc import BaseApiHandler
from xiaodi.api.auth import require_auth
from xiaodi.api.mysql import Permission
from xiaodi.common.reqparse import RequestParser


class UserHandler(BaseApiHandler):
    @require_auth(Permission.COMMON)
    def get(self):
        self.write_success({
           'user': (yield get_user(self._G.user))
        })

    @require_auth(Permission.COMMON)
    def put(self):
        args = RequestParser(). \
            add_body_argument('nickname'). \
            add_file_argument('headimg'). \
            add_body_argument('sex'). \
            add_body_argument('introduction'). \
            parse_args(self)

        yield put_user(self._G.user, nickname=args.nickname, headimg=args.headimg,
                       sex=args.sex, introduction=args.introduction)

        self.write_success()


class ChangePasswordHandler(BaseApiHandler):
    @require_auth(Permission.COMMON)
    def put(self):
        args = RequestParser(). \
            add_body_argument('old_password', required=True). \
            add_body_argument('password', required=True). \
            parse_args(self)

        yield do_change_password(self._G.user, args.old_password, args.password)

        self.write_success()


class ForgetPasswordHandler(BaseApiHandler):
    @require_auth(Permission.ADMIN)
    def post(self):
        args = RequestParser(). \
            add_body_argument('phone', required=True, filter='\d{11}'). \
            add_body_argument('password', required=True). \
            parse_args(self)

        yield do_forget_password(args.phone, args.password)

        self.write_success()

