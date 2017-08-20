# coding=utf-8
import hashlib
import logging

from xiaodi.common.pxfilter import XssHtml
from xiaodi.common.redis_client import get_aredis_client
from xiaodi.settings import IMAGE_SERVER, TIME_FORMAT

LOG = logging.getLogger(__name__)


def xss_filter(text):
    if text is None or isinstance(text, (bool, int, float)):
        return text

    parser = XssHtml()
    parser.feed(text)
    parser.close()

    return parser.getHtml()


def hash_str(text):
    return hashlib.md5(text).hexdigest()


def change_headimg_url(image_file_url):
    try:
        new_url = IMAGE_SERVER + str(image_file_url)
    except TypeError as e:
        LOG.exception(str(e))
        return None
    else:
        return new_url


def tranform_timestamp(time_str, format=TIME_FORMAT):
    import time

    return time.mktime(time.strptime(str(time_str), format))


def tranform_utctime(time_str, format=TIME_FORMAT):
    import random
    from datetime import datetime, timedelta

    timestamp = tranform_timestamp(time_str, format)
    utctime = datetime.utcfromtimestamp(timestamp)
    # 给只精确到分的时间加上随机秒数
    if format != TIME_FORMAT:
        utctime = utctime + timedelta(seconds=random.randint(0, 59))

    return utctime


def gen_random_str(lenght):
    import random
    import string

    return ''.join(random.sample(string.ascii_letters + string.digits, lenght))


def gen_temp_object(**kwargs):
    from collections import namedtuple

    return namedtuple('TempObject', kwargs.keys())(*kwargs.values())


def publish_redis_event(message):
    from xiaodi.settings import REDIS_EVENT_DB, REDIS_CHANNEL

    client = get_aredis_client(REDIS_EVENT_DB)
    client.publish(REDIS_CHANNEL, message)
