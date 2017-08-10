# coding=utf-8
from enum import Enum
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

from const import DEFAULT_THREADS
from xiaodi.api.mysql import db


class TaskNames(Enum):
    EXECUTE_SQL = 'execute_sql'
    SEND_EMAIL = 'send_email'


class ExecuteSqlTask(object):

    executor = ThreadPoolExecutor(DEFAULT_THREADS)

    # only IO intensive can get help from thread pool
    # because of the GIL. if the task is CPU intensive,
    # using process pool is better.
    @run_on_executor
    def run(self, sqls=None):
        sqls_ = sqls if isinstance(sqls, list) else [sqls]

        object_ = db.session
        for sql in sqls_:
            if sql[1] is not None:
                object_ = getattr(object_, sql[0])(sql[1])
            else:
                object_ = getattr(object_, sql[0])()

        return object_ if object_ is not None else None


class SendEmailTask(object):
    pass


class CommonTaskFactory(object):
    @classmethod
    def get_task_instance(cls, name):
        return {
            TaskNames.EXECUTE_SQL.value: ExecuteSqlTask(),
            TaskNames.SEND_EMAIL.value: SendEmailTask()
        }[name]
