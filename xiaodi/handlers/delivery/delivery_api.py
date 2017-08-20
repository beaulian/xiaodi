# coding=utf-8
from delivery import publish_delivery
from delivery import get_delivery
from tornado.httputil import HTTPFile
from xiaodi.api.abc import BaseApiHandler
from xiaodi.api.auth import require_auth
from xiaodi.api.mysql import Permission
from xiaodi.common.reqparse import RequestParser

format_addr = lambda t: ''.join(t.split()[0:3:2])


class DeliveryHandler(BaseApiHandler):
    @require_auth(Permission.COMMON, identified=True, innocence=True, xiaodier=True)
    def post(self):
        args = RequestParser(). \
            add_body_argument('source', required=True, type=format_addr). \
            add_body_argument('destination', required=True, type=format_addr). \
            add_file_argument('thumbnail', type=HTTPFile). \
            add_body_argument('type', required=True). \
            add_body_argument('weight', required=True, type=int). \
            add_body_argument('reward', required=True, type=int). \
            add_body_argument('contact', required=True, filter='\d{11}'). \
            add_body_argument('deadline', required=True). \
            add_body_argument('describe'). \
            parse_args(self)

        id_ = yield publish_delivery(self._G.user, **args)
        self.write_success({'id': id_})

    def get(self):
        args = RequestParser(). \
            add_query_argument('school', default='cqu'). \
            add_query_argument('sort', type=int, default=0, filter='[01]'). \
            add_query_argument('ascend', type=int, default=0, filter='[01]'). \
            add_query_argument('keyword'). \
            add_query_argument('page_num', type=int, default=1, filter='\d+'). \
            parse_args(self)

        deliveries = yield get_delivery(**args)
        self.write_success({'deliveries': deliveries})




