# coding=utf-8
import os
import logging
from tornado import gen
from xiaodi.api.errors import invalid_argument_error
from xiaodi.common.utils import hash_str
from xiaodi.common.tasks import CommonTaskFactory, TaskNames

LOG = logging.getLogger(__name__)


def allow_image_format(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ["jpg", "jpeg", "png"]


def allow_image_size(_file):
    return len(_file["body"]) <= 2*1024*1024


@gen.coroutine
def save_image_to_oss(file_, storge_path, key, when_fail=None):
    if not allow_image_format(file_["filename"]):
        raise gen.Return(invalid_argument_error('invalid image format: only jpg, ipeg, png is supported'))
    if not allow_image_size(file_):
        raise gen.Return(invalid_argument_error('invalid image size: less than or equal 2M is required'))

    seed = hash_str(os.path.splitext(file_["filename"])[0] + key)
    image_filename = storge_path + seed + os.path.splitext(file_["filename"])[1]

    result = yield CommonTaskFactory. \
        get_task(TaskNames.PROCESS_IMAGE.value). \
        run('upload_file', file_["body"], image_filename)
    if result:
        raise gen.Return(image_filename)
    else:
        raise gen.Return(when_fail)


@gen.coroutine
def remove_image_from_oss(filename):
    result = yield CommonTaskFactory. \
        get_task(TaskNames.PROCESS_IMAGE.value). \
        run('delete_file', filename)

    raise gen.Return(result)
