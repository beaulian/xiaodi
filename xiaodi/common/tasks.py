# coding=utf-8
import logging
from enum import Enum
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

from const import DEFAULT_THREADS
from xiaodi.api.mysql import db, ExecuteSqlError
from xiaodi.spider import get_spider
from xiaodi.api.errors import internal_server_error

LOG = logging.getLogger(__name__)


class TaskNames(Enum):
    EXECUTE_SQL = 'execute_sql'
    SEND_EMAIL = 'send_email'
    IDENTIFY_USER = 'identify_user'


class Task(object):
    # only IO intensive can get help from thread pool
    # because of the GIL. if the task is CPU intensive,
    # using process pool is better.
    executor = ThreadPoolExecutor(DEFAULT_THREADS)

    @run_on_executor
    def run(self):
        raise NotImplementedError


class ExecuteSqlTask(Task):
    @run_on_executor
    def run(self, sqls=None):
        sqls_ = sqls if isinstance(sqls, list) else [sqls]

        object_ = db.session
        for sql in sqls_:
            try:
                if sql[1] is not None:
                    object_ = getattr(object_, sql[0])(sql[1])
                else:
                    object_ = getattr(object_, sql[0])()
            except ExecuteSqlError as e:
                LOG.exception(str(e))
                db.session.rollback()
            except Exception as e:
                LOG.exception(str(e))
                return internal_server_error(e.message)

        return object_ if object_ is not None else None


class SendEmailTask(Task):
    pass


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
        }[name]
