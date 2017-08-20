# -*- coding: UTF-8 -*-

import oss2
import logging
from xiaodi.common.cache import Cache

LOG = logging.getLogger(__name__)


class OSSFile(object):

    def __init__(self, auth=(), endpoint=None, bucket_name=None, timeout=5):
        # 注意考虑超时的情况
        self._bucket = oss2.Bucket(auth=oss2.Auth(*auth),
                                   endpoint=endpoint,
                                   bucket_name=bucket_name,
                                   connect_timeout=timeout)

    def test(self):
        from itertools import islice
        for b in islice(oss2.ObjectIterator(self._bucket), 0, 100):
            print b.key

    def upload_file(self, local_file, remote_file):
        self._bucket.put_object(remote_file, local_file)

    def delete_file(self, remote_file):
        self._bucket.delete_object(remote_file)

    def __str__(self):
        return 'OSSFile'


@Cache.cache_in_request(async=False)
def get_ossfile_client(**kwargs):
    return OSSFile(**kwargs)


if __name__ == '__main__':
    ossfile2 = OSSFile()
    ossfile2.test()
