# coding=utf-8
import os
import logging

from xiaodi.common.utils import hash_str
from xiaodi.common.oss_bucket_api import ossfile

LOG = logging.getLogger(__name__)


def allow_image_format(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ["jpg", "jpeg", "png"]


def allow_image_size(_file):
    return len(_file["body"]) <= 2*1024*1024


def save_image_to_oss(_file, storge_path, key):
    seed = hash_str(os.path.splitext(_file["filename"])[0] + key)
    image_filename = storge_path + seed + os.path.splitext(_file["filename"])[1]
    ossfile.upload_file(_file["body"], image_filename)
    return image_filename


def remove_image(filename):
    ossfile.delete_file(filename)
