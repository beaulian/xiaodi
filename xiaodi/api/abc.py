# coding=utf-8
import logging

from tornado.gen import coroutine
from tornado.web import asynchronous
from tornado.web import RequestHandler

LOG = logging.getLogger(__name__)


class GenAsyncMetaclass(type):
    def __new__(cls, clsname, bases, attrs):
        allow_method = ['get', 'put', 'delete', 'post', 'options', 'patch']
        for method in attrs:
            if method.lower() in allow_method:
                attrs[method] = coroutine(asynchronous(attrs[method]))

        return super(GenAsyncMetaclass, cls).__new__(cls, clsname, bases, attrs)


class DictWithAttrs(dict):
    def __setattr__(self, key, value):
        super(DictWithAttrs, self).__setitem__(key, value)

    def __getattr__(self, key):
        return super(DictWithAttrs, self).__getitem__(key)


class BaseApiHandler(RequestHandler):

    __metaclass__ = GenAsyncMetaclass

    def prepare(self):
        self._G = DictWithAttrs()

    def on_finish(self):
        pass

    def async_write(self, data, finish=True):
        self.write(data)
        # disconnect long connection
        if finish:
            self.finish()

    def write_error(self, status_code, **kwargs):
        try:
            exc_info = kwargs.pop('exc_info')
            e = exc_info[1]
            self.set_status(status_code)
            self.async_write(str(e))
        except Exception as e:
            LOG.exception(str(e))
            super(BaseApiHandler, self).write_error(status_code, **kwargs)

    # private method
    def __set_cross_domain_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Max-Age', 1000)
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, DELETE, OPTIONS')
        self.set_header('Access-Control-Allow-Headers', '*')

    def set_default_headers(self):
        self.__set_cross_domain_headers()
        self.set_header('Content-type', 'application/json')

    def options(self, *args):
        self.__set_cross_domain_headers()

    @property
    def db(self):
        return self.application.db

    @property
    def settings(self):
        return self.application.settings
