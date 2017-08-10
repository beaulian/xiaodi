# coding=utf-8
import hashlib
import logging

from xiaodi.common.pxfilter import XssHtml
from xiaodi.settings import IMAGE_SERVER

LOG = logging.getLogger(__name__)


def xss_filter(text):
    parser = XssHtml()
    if not isinstance(text, bool) and text is not None:
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
