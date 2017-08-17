# coding=utf-8
import re
import logging
from http_request import self_requests

LOG = logging.getLogger(__name__)


def cqu_spider(sid, password, truename):
    login_url = "http://ids.cqu.edu.cn/amserver/UI/Login"
    info_url = "http://i.cqu.edu.cn/user/userInfo.do"

    postdata = {
        "IDToken0": "",
        "IDToken1": sid,
        "IDToken2": password,
        "IDButton": "Submit",
        "goto": "",
        "encoded": "true",
        "gx_charset": "UTF-8"
    }
    self_requests.post(login_url, data=postdata)
    r = self_requests.get(info_url)
    r.encoding = 'utf-8'

    try:
        result = re.search(r"姓名[\s\S]+{truename}\s+?<".format(
            truename=truename).decode("utf-8"), r.text.decode("utf-8"))
    except (UnicodeDecodeError, UnicodeEncodeError) as e:
        LOG.exception(str(e))

        import sys
        reload(sys)
        sys.setdefaultencoding("utf-8")

        result = re.search(r"姓名[\s\S]+{truename}\s+?<".format(
            truename=truename).decode("utf-8"), r.text.decode('utf-8'))

    return result
