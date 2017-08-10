import celeryconfig
from celery import Celery

app = Celery()
app.config_from_object(celeryconfig)
