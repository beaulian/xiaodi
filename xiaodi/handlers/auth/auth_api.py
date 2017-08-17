# coding=utf-8
from tornado.httputil import HTTPFile
from auth import login_authentication
from auth import manager_login_authentication
from auth import register_user
from auth import identify_user
from auth import fulltime_request
from xiaodi.api.abc import BaseApiHandler
from xiaodi.api.auth import require_auth
from xiaodi.api.auth import AuthorizerHelper
from xiaodi.api.mysql import Permission
from xiaodi.common.reqparse import RequestParser


class LoginHandler(BaseApiHandler):
    def post(self):
        args = RequestParser(). \
            add_body_argument('phone', required=True, filter='\d{11}'). \
            add_body_argument('password', required=True). \
            parse_args(self)

        user = yield login_authentication(args.phone, args.password)

        self.write_success({
                "username": user.username,
                "token": AuthorizerHelper.generate_token(user)
        })

    def put(self):
        self.write_success({
            "token": AuthorizerHelper.generate_token(self._G.user)
        })


class ManagerLoginHandler(BaseApiHandler):
    def post(self):
        args = RequestParser(). \
            add_body_argument('username', required=True). \
            add_body_argument('password', required=True). \
            parse_args(self)

        user = yield manager_login_authentication(username=args.username, password=args.password)

        self.write_success({
                "username": user.username,
                "token": AuthorizerHelper.generate_token(user)
        })

    def put(self):
        self.write_success({
            "token": AuthorizerHelper.generate_token(self._G.user)
        })


class RegisterHandler(BaseApiHandler):
    @require_auth(Permission.ADMIN)
    def post(self):
        args = RequestParser(). \
            add_body_argument('nickname', required=True). \
            add_body_argument('phone', required=True, filter='\d{11}'). \
            add_file_argument('headimg', type=HTTPFile). \
            add_body_argument('sex', type=str, default='男'). \
            add_body_argument('password', required=True, filter='[\w\d_@.-]{6,}'). \
            add_body_argument('unique_id'). \
            add_body_argument('code'). \
            parse_args(self)

        user = yield register_user(password=args.password, nickname=args.nickname, code=args.code,
                                   headimg=args.headimg, sex=args.sex, phone=args.phone,
                                   unique_id=args.unique_id)

        self.write_success({
            "user": user.to_json(),
            "token": AuthorizerHelper.generate_token(user)
        })


class SchoolAuthHandler(BaseApiHandler):
    @require_auth(Permission.COMMON)
    def post(self):
        args = RequestParser(). \
            add_body_argument('truename', required=True). \
            add_body_argument('school', type=str, default='cqu'). \
            add_body_argument('role', type=str, required=True). \
            add_body_argument('school_id', required=True). \
            add_body_argument('password', required=True). \
            parse_args(self)

        yield identify_user(self._G.user, role=args.role, school=args.school, sid=args.school_id,
                            password=args.password, truename=args.truename)

        self.write_success()


class FulltimeRequestAuthHandler(BaseApiHandler):
    @require_auth(Permission.COMMON, identified=True, innocence=True)
    def post(self):
        args = RequestParser(). \
            add_body_argument('address', required=True, filter='\S+\s+\S+'). \
            parse_args(self)

        yield fulltime_request(self._G.user, address=args.address)

        self.write_success()



