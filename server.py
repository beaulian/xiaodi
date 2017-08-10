# coding=utf-8
import os
import time
import logging
import schedule
import threading
import tcelery
import tornado.httpserver
import tornado.ioloop
import tornado.locale
import tornado.web
from tornado.options import define, options
from multiprocessing import Lock

from xiaodi import settings as gsettings
from xiaodi.api.mysql import db, start_update_engagement
from xiaodi.url import handlers
from xiaodi.celery_tasks.app import app

define("port", default=gsettings.LISTEN_PORT, type=int, help="run no the given port")


tcelery.setup_nonblocking_producer(celery_app=app)

LOG = logging.getLogger(__name__)
LOCK = Lock()


class Application(tornado.web.Application):
    def __init__(self):
        ''' load global settings, which use by
            self.application.gsettings in tornado.web.RequestHandler,
            self.gsettings in tornado.web.Application'
        '''
        self.settings = gsettings

        settings = {
            "debug": self.settings.DEBUG,
            "gzip": self.settings.GZIP,
        }
        # init db
        self.db = db

        super(Application, self).__init__(handlers, **settings)


def __start_schedule_deamon():
    def schedule_run():
        while True:
            schedule.run_pending()
            time.sleep(1)

    t = threading.Thread(target=schedule_run)
    t.setDaemon(True)
    t.start()


def __init():
    if LOCK.acquire(block=False):
        LOG.info('Acquire process lock succeed at process: %d, start job' % os.getpid())
        start_update_engagement()
        __start_schedule_deamon()
    else:
        LOG.info("Acquire file lock failed, skip start job")

__init()


def main():
    tornado.options.parse_command_line()

    LOG.info('start run server on %s:%s' % (gsettings.LISTEN_ADDRESS, options.port))
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address=gsettings.LISTEN_ADDRESS)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
