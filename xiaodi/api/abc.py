# coding=utf-8
import types
import logging

from tornado.gen import coroutine
from tornado.web import asynchronous
from tornado.web import RequestHandler
from cached_property import cached_property
from tornado.web import HTTPError
from xiaodi.api.errors import HTTPAPIError
from xiaodi.api.errors import INTERNAL_SERVER_ERROR
from xiaodi.api.errors import BAD_REQUEST_ERROR

LOG = logging.getLogger(__name__)


class GenAsyncMetaclass(type):
    def __new__(cls, clsname, bases, attrs):
        allow_method = ['get', 'put', 'delete', 'post', 'options', 'patch']
        for method in attrs:
            if method.lower() in allow_method:
                attrs[method] = coroutine(asynchronous(attrs[method]))

        return super(GenAsyncMetaclass, cls).__new__(cls, clsname, bases, attrs)


class Namespace(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class BaseApiHandler(RequestHandler):

    __metaclass__ = GenAsyncMetaclass

    def prepare(self):
        self._G = Namespace()

    def on_finish(self):
        self.set_header("Content-Type", "application/json; charset=UTF-8")

    def _async_write(self, data, finish=True):
        self.write(data)
        # disconnect long connection
        if finish:
            self.finish()

    def write_success(self, data=None, finish=True):
        assert isinstance(data, (types.NoneType, dict)), 'data must be NoneType or dict'
        self._async_write(dict((data or {}), **{'status': 'success'}), finish=finish)

    def write_error(self, status_code, **kwargs):
        try:
            exc_info = kwargs.pop('exc_info')
            e = exc_info[1]
            if isinstance(e, HTTPAPIError):
                pass
            elif isinstance(e, HTTPError):
                e = HTTPAPIError(BAD_REQUEST_ERROR, e.log_message, e.status_code)
            else:
                e = HTTPAPIError(INTERNAL_SERVER_ERROR, str(e), 500)
            self.set_status(status_code)
            self._async_write(str(e))
        except Exception as e:
            LOG.exception(str(e))
            return super(BaseApiHandler, self).write_error(status_code, **kwargs)

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

    @cached_property
    def db(self):
        return self.application.db

    @property
    def settings(self):
        return self.application.settings
