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

# mysql setting
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
DB_NAME = "xxx"
MYSQL_USERNAME = "xxx"
MYSQL_PASSWORD = "xxx"

# redis setting
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_PASSWORD = "xxx"
REDIS_TASK_DB = "xxx"
REDIS_REWARD_DB = "xxx"
REDIS_EVENT_DB = "xxx"

REDIS_CHANNEL = 'sse'

# security
SECRET_CODE = "xxx"
# admin account
SU_ADMIN = "xxx"
SU_TOKEN = "xxx"

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
XIAODIER = (FULLTIME_ROLE, SPECIAL_FULLTIME_ROLE)

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

AUTO_DELETE_QUEUE = "auto_delete"
AUTO_FINISH_QUEUE = "auto_finish"
AUTO_FINISH_DELAY = 1

PUBLISH_AWARD = ('first_publish', '第一次发布代送', 50)
RECEIVE_AWARD = ('first_receive', '第一次领取代送', 50)
SENDREWARD_AWARD = ('first_sendreward', '第一次赠送好友笑点', 10)

SHARE_ENGAGEMENT = ('share', 10)
PUBLISH_ENGAGEMENT = ('publish', 20)
RECEIVE_ENGAGEMENT = ('receive', 20)
RECAHRE_ENGAGEMENT = ('recharge', 30)

OSS_ACCESS_KEY_ID = "xxx"
OSS_ACCESS_KEY_SECRET = "xxx"
OSS_ENDPOINT = "xxx"
OSS_XIAODI_BUCKET = "xxx"

# email setting
MAIL_HOST = "xxx"
MAIL_SENDER = "xxx"
MAIL_PASSWORD = "xxx"
MAIL_RECEIVER_LIST = ["xxx", ]

ADMIN1_USERNAME = 'xxx'
ADMIN1_PASSWORD = 'xxx'
ADMIN2_USERNAME = 'xxx'
ADMIN2_PASSWORD = 'xxx'

# max number of  per page
MAX_DELIVERY_PER_PAGE = 10
MAX_ENGAGEMENT_PER_PAGE = 8
MAX_POINT_PER_PAGE = 8
MAX_POINT_RECORD_PER_PAGE = 8
MAX_MESSAGE_PER_PAGE = 6
MAX_COMPLAINT_PER_PAGE = 7
MAX_USER_PER_PAGE = 10
MAX_PRESENTRECORD_PER_PAGE = 7
MAX_MONEYRECORD_PER_PAGE = 7
MAX_BLACKLIST_PER_PAGE = 7
MAX_REQUESTRECORD_PER_PAGE = 7
MAX_SPECIALUSER_PER_PAGE = 8
MAX_ASSESSMENT_PER_PAGE = 8

ORDER_FIELDS = ['reward', 'weight']

XIAODI_PROCESS_LOCK = '/tmp/xiaodi.lock'


