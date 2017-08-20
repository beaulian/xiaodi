# coding=utf-8
import logging
from enum import Enum
from oss2.exceptions import RequestError
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

from const import DEFAULT_THREADS
from xiaodi.api.mysql import session, ExecuteSqlError
from xiaodi.spider import get_spider
from xiaodi.api.errors import internal_server_error
from xiaodi.common.oss_bucket_api import get_ossfile_client
from xiaodi.settings import OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET
from xiaodi.settings import OSS_ENDPOINT, OSS_XIAODI_BUCKET

import smtplib
from email.mime.text import MIMEText
from xiaodi.settings import MAIL_HOST, MAIL_PASSWORD
from xiaodi.settings import MAIL_SENDER, MAIL_RECEIVER_LIST

LOG = logging.getLogger(__name__)


class TaskNames(Enum):
    EXECUTE_SQL = 'execute_sql'
    SEND_EMAIL = 'send_email'
    IDENTIFY_USER = 'identify_user'
    PROCESS_IMAGE = 'process_image'


class Task(object):
    # only IO intensive can get help from thread pool
    # because of the GIL. if the task is CPU intensive,
    # using process pool is better.
    executor = ThreadPoolExecutor(DEFAULT_THREADS)

    @run_on_executor
    def run(self, *args, **kwargs):
        raise NotImplementedError


class ExecuteSqlTask(Task):
    @run_on_executor
    def run(self, sqls=None):
        sqls_ = sqls if isinstance(sqls, list) else [sqls]

        object_ = session
        for sql in sqls_:
            try:
                if sql[1] is None:
                    object_ = getattr(object_, sql[0])()
                elif isinstance(sql[1], tuple):
                    object_ = getattr(object_, sql[0])(*list(sql[1]))
                elif isinstance(sql[1], dict):
                    object_ = getattr(object_, sql[0])(**sql[1])
                else:
                    object_ = getattr(object_, sql[0])(sql[1])
            except ExecuteSqlError as e:
                LOG.exception('execute sqls %s failed with error: %s' % (str(sql), str(e)))
                session.rollback()
                raise ExecuteSqlError(e.message)
            except Exception as e:
                LOG.exception(str(e))
                return internal_server_error(e.message)

        return object_ if object_ is not None else None


class ProcessImageTask(Task):
    @run_on_executor
    def run(self, operator, *args):
        try:
            ossfile = get_ossfile_client(auth=(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET),
                                         endpoint=OSS_ENDPOINT, bucket_name=OSS_XIAODI_BUCKET)
            getattr(ossfile, operator)(*args)
        except RequestError as e:
            LOG.error('connect oss timeout: %s' % str(e))
            return False
        except Exception as e:
            LOG.error('catch unkown error: %s' % str(e))
            return False
        else:
            return True


class SendEmailTask(Task):
    @run_on_executor
    def run(self, nickname=None, content=None, image=None):

        text = content + "<br>" + "<img src={image} />".format(image=image) \
                if image is not None else content
        msg = MIMEText(text, _subtype="html", _charset="utf-8")
        msg["Subject"] = "用户反馈"
        msg["From"] = nickname + "<" + MAIL_SENDER + ">"
        msg["To"] = ",".join(MAIL_RECEIVER_LIST)

        try:
            server = smtplib.SMTP()
            server.connect(MAIL_HOST)
            server.starttls()
            server.login(MAIL_SENDER, MAIL_PASSWORD)
            server.sendmail(MAIL_SENDER, MAIL_RECEIVER_LIST, msg.as_string())
            server.close()
        except Exception as e:
            LOG.error('send mail failed with error: %s' % str(e))
            return False
        return True


class IdentifyUserTask(Task):
    @run_on_executor
    def run(self, school=None, sid=None, password=None, truename=None):
        spider = get_spider(school)
        if spider is None:
            return None
        return spider(sid, password, truename)


class CommonTaskFactory(object):
    @classmethod
    def get_task(cls, name):
        return {
            TaskNames.EXECUTE_SQL.value: ExecuteSqlTask(),
            TaskNames.SEND_EMAIL.value: SendEmailTask(),
            TaskNames.IDENTIFY_USER.value: IdentifyUserTask(),
            TaskNames.PROCESS_IMAGE.value: ProcessImageTask(),
        }[name]
