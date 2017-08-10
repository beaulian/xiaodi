# coding=utf-8

from auth_api import LoginHandler
from auth_api import RegisterHandler
from auth_api import ManagerLoginHandler

__all__ = ['handlers']

handlers = [
    (r"/user/register", RegisterHandler),
    (r"/user/login", LoginHandler),
    (r"/manager/login", ManagerLoginHandler),
]
