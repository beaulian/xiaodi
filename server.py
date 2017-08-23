# coding=utf-8
import os
import time
import logging
import schedule
import threading
import tornado.httpserver
import tornado.ioloop
import tornado.locale
import tornado.web
from tornado.options import define, options
from fasteners import process_lock

from xiaodi import settings as gsettings
from xiaodi.api.mysql import start_update_engagement
from xiaodi.handlers.delivery.delivery_utils import auto_delete_delivery
from xiaodi.handlers.delivery.delivery_utils import auto_finish_delivery
from xiaodi.url import handlers

define("port", default=gsettings.LISTEN_PORT, type=int, help="run no the given port")

LOG = logging.getLogger(__name__)
# 不能用multiprocess的锁，因为multiprocess的锁只适用于父子进程间的锁
LOCK = process_lock.InterProcessLock(gsettings.XIAODI_PROCESS_LOCK)


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
    if LOCK.acquire(blocking=False):
        LOG.info('Acquire process lock succeed at process: %d, start job' % os.getpid())
        start_update_engagement()
        auto_delete_delivery()
        auto_finish_delivery()
        __start_schedule_deamon()
    else:
        LOG.info("Acquire file lock failed, skip start job")


def main():
    tornado.options.parse_command_line()

    __init()
    LOG.info('start run server on %s:%s' % (gsettings.LISTEN_ADDRESS, options.port))
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port, address=gsettings.LISTEN_ADDRESS)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
