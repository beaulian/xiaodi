# coding=utf-8
import os
import re

DEBUG = True
# gzip setting
GZIP = True

# system port
LISTEN_ADDRESS = "0.0.0.0"
LISTEN_PORT = 8000
PREFIX_URL = "http://api.xiaodi16.com"

# mongodb setting
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
DB_NAME = "xxxxx"
MYSQL_USERNAME = "xxxxx"
MYSQL_PASSWORD = "xxxxx"

# security
SECRET_CODE = "xxxxx"

# admin account
SU_ADMIN = "xxxx"
SU_TOKEN = "xxxx"

# default path of static path
DEFAULT_PYTHON_PATH = os.getcwd()

# default online headimg path
DEFAULT_HEADIMG = "img/headimg/default.jpg"
# DEFAULT_WIDTH = 200

# default thumbnail path
DEFAULT_THUMBNAIL = "img/thumbnail/default_{type}.jpg"
# DEFAULT_THUMBNAIL_WIDTH = 300

# default point
DEFAULT_POINT = 300
PER_SEND_POINT = 10

# credibility
DEFAULT_CREDIBILITY = 0
MAX_CREDIBILITY = 5

# invite
INVITE_AWARD_POINT = 20

# added point by signing in
DAY_POINT = 5
WEEK_DAY_REWARD_POINT = 10

# oss services
IMAGE_SERVER = "http://img.xiaodi16.com/"
OSS_HEADIMG_PATH = "img/headimg/"
OSS_THUMBNAIL_PATH = "img/thumbnail/"
OSS_FEEDBACK_PATH = "img/feedback/"
OSS_BANNER_PATH = "img/banner/"

# user role
COMMON_ROLE = "common"
SERVICE_ROLE = "service"
FULLTIME_ROLE = "fulltime"
SPECIAL_FULLTIME_ROLE = "special"
