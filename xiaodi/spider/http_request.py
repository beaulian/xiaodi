# coding=utf-8
import functools
import requests
from xiaodi.common.const import DEFAULT_HTTP_TIMEOUT

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, \
                         like Gecko) Chrome/38.0.2125.122 Safari/537.36"
}


class Requests(object):
    def __init__(self):
        self._session = requests.Session()

    def __getattr__(self, key):
        return functools.partial(getattr(self._session, key),
                                 headers=headers, timeout=DEFAULT_HTTP_TIMEOUT)


self_requests = Requests()
