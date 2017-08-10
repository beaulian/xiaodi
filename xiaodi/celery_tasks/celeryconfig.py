# -*- coding: utf-8 -*-
from __future__ import absolute_import

from kombu import Queue, Exchange
from celery.schedules import crontab

CELERY_IMPORTS = ("tasks", )
CELERY_RESULT_BACKEND = "amqp"
BROKER_URL = "amqp://xxx:xxx@127.0.0.1:5672//"
CELERY_TASK_RESULT_EXPIRES = 300
CELERY_TIMEZONE = 'UTC'

CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']

CELERYBEAT_SCHEDULE = {
    'auto_delete_delivery': {
        'task': 'xiaodi.celery_tasks.tasks.auto_delete_delivery',
        'schedule': crontab(minute="*/5"),
        'args': (),
        "options": {'queue': 'delete'}
    },
    'auto_finish_delivery': {
        'task': 'xiaodi.celery_tasks.tasks.auto_finish_delivery',
        'schedule': crontab(minute="*/30"),
        'args': (),
        "options": {'queue': 'finish'}
    }
}

CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('delete', Exchange('celery_tasks'), routing_key='celery_tasks.delivery_delete'),
    Queue('finish', Exchange('celery_tasks'), routing_key='celery_tasks.delivery_finish'),
)

CELERY_ROUTES = {
    'xiaodi.celery_tasks.tasks.auto_delete_delivery': {'queue': 'delete', 'routing_key': 'celery_tasks.delivery_delete'},
    'xiaodi.celery_tasks.tasks.auto_finish_delivery': {'queue': 'finish', 'routing_key': 'celery_tasks.delivery_finish'},
}
