# -*- coding: UTF-8 -*-

import oss2


auth = oss2.Auth('xxx', 'xxx')
endpoint = 'http://oss-cn-hangzhou.aliyuncs.com'


class OSSFile(object):

    def __init__(self):
        self._bucket = oss2.Bucket(auth, endpoint, "xiaodi16")

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

ossfile = OSSFile()


if __name__ == '__main__':
    ossfile2 = OSSFile()
    ossfile2.test()
