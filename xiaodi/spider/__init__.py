# coding=utf-8
import logging
from spiders import cqu_spider

LOG = logging.getLogger(__name__)


def get_spider(school):
    try:
        return eval(school.lower() + '_spider')
    except (NameError, SyntaxError) as e:
        LOG.exception('no such school: %s, failed with %s' % (school, str(e)))
        return None
