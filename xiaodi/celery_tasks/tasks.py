# coding=utf-8
import pickle

from celery import exceptions
from celery.utils.log import get_task_logger
from app import app as celery
from xiaodi.api.mysql import *

LOG = get_task_logger(__name__)


