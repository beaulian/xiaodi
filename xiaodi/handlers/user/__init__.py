# coding=utf-8

from user_api import UserHandler
from user_api import ChangePasswordHandler
from user_api import ForgetPasswordHandler

__all__ = ['handlers']

handlers = [
    (r"/user/self", UserHandler),
    (r"/user/password", ChangePasswordHandler),
    (r"/user/forget_password", ForgetPasswordHandler),
]
