# coding=utf-8
from delivery_api import DeliveryHandler
from xiaodi.common.tornado_sse import SSEHandler

__all__ = ['handlers']


handlers = [
    (r'/delivery', DeliveryHandler),
    (r'/ws', SSEHandler),
]