# coding=utf-8
import six
import json
import schedule
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy import Column, String, ForeignKey, Integer, Float, DateTime, Boolean

from xiaodi.settings import MYSQL_HOST
from xiaodi.settings import MYSQL_PORT
from xiaodi.settings import MYSQL_USERNAME
from xiaodi.settings import MYSQL_PASSWORD
from xiaodi.settings import DB_NAME
from xiaodi.settings import ADMIN1_USERNAME
from xiaodi.settings import ADMIN1_PASSWORD
from xiaodi.settings import ADMIN2_USERNAME
from xiaodi.settings import ADMIN2_PASSWORD
from xiaodi.common.const import DB_STRING_LENGTH
from xiaodi.common.utils import change_headimg_url

engine = create_engine('mysql+mysqldb://%s:%s@%s:%d/%s?charset=utf8' %
                       (MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_HOST,
                        MYSQL_PORT, DB_NAME))
DBSession = sessionmaker(bind=engine)


class ExecuteSqlError(InvalidRequestError):
    pass


def _convert_attr_to_dict(cls):
    attrs = {}
    for attr in dir(cls):
        value = getattr(cls, attr)
        if not attr.startswith('__') and not attr.endswith('V') \
                and isinstance(value, six.string_types):
            if cls.__class__.__name__ == 'User':
                if attr == 'headimg':
                    attrs.update({attr: change_headimg_url(value)})
                elif attr == 'password':
                    continue
                else:
                    attrs.update({attr: value})
            else:
                if isinstance(value, datetime):
                    attrs.update({attr: str(value)})
                else:
                    attrs.update({attr: value})
    return attrs


def _init_cls(cls):
    setattr(cls, '__tablename__', cls.__name__)
    setattr(cls, 'id', Column(Integer, primary_key=True, autoincrement=True))
    for _str in getattr(cls, 'stringV', []):
        setattr(cls, _str, Column(String(DB_STRING_LENGTH)))
    for _int in getattr(cls, 'integerV', []):
        setattr(cls, _int, Column(Integer))
    for _bool in getattr(cls, 'boolV', []):
        setattr(cls, _bool, Column(Boolean))
    for _float in getattr(cls, 'floatV', []):
        setattr(cls, _float, Column(Float))
    for _time in getattr(cls, 'timeV', []):
        setattr(cls, _time, Column(DateTime, default=datetime.utcnow))
    for key, value in getattr(cls, 'foreignKeyV', {}).iteritems():
        setattr(cls, key, Column(Integer, ForeignKey(value), primary_key=True))
    setattr(cls, 'to_json', _convert_attr_to_dict)


class ModelMetaclass(DeclarativeMeta):
    def __init__(self, clsname, bases, dct):
        _init_cls(self)

        super(ModelMetaclass, self).__init__(clsname, bases, dct)

Base = declarative_base(metaclass=ModelMetaclass)


class Permission(object):
    COMMON = 'user'
    MANAGER = 'manager'
    ADMIN = 'admin'


class User(Base):
    stringV = ['username', 'password', 'nickname', 'headimg', 'phone',
               'school', 'campus', 'hostel', 'role', 'unique_id',
               'code', 'sex', 'introduction']
    integerV = ['original_point', 'bright_point']
    floatV = ['credibility']
    timeV = ['register_time']
    boolV = ['identified']


class Auth(Base):
    stringV = ['truename', 'school_id', 'school_role', 'identifier']
    foreignKeyV = {'user_id': 'User.id'}


class Admin(Base):
    stringV = ['username', 'password']


class Engagement(Base):
    stringV = ['engagement']
    foreignKeyV = {'user_id': 'User.id'}


class PointRecord(Base):
    stringV = ['type', 'number']
    integerV = ['balance']
    timeV = ['time']
    foreignKeyV = {'user_id': 'User.id'}


class Assessment(Base):
    stringV = ['content']
    floatV = ['star']
    timeV = ['time']
    foreignKeyV = {'user_from': 'User.id', 'user_to': 'User.id'}


class Msg(Base):
    stringV = ['title', 'content', 'banner', 'link', 'notice_set_id']
    integerV = ['read_count', 'state']
    foreignKeyV = {'user_to': 'User.id'}


class Task(Base):
    stringV = ['school', 'thumbnail', 'weight', 'type',
               'source', 'destination', 'contact', 'describe']
    integerV = ['reward', 'state']
    timeV = ['deadline', 'time']
    foreignKeyV = {'puser_id': 'User.id', 'ruser_id': 'User.id'}


class Sign(Base):
    stringV = ['record']
    integerV = ['day']
    timeV = ['last_sign']
    foreignKeyV = {'user_id': 'User.id'}


class Award(Base):
    stringV = ['type']
    foreignKeyV = {'user_id': 'User.id'}


class Withdrawal(Base):
    integerV = ['level', 'count']
    timeV = ['time']
    foreignKeyV = {'user_id': 'User.id'}


class Present(Base):
    stringV = ['alipay_account', 'limit']
    integerV = ['month']
    foreignKeyV = {'user_id': 'User.id'}


class PresentRecord(Base):
    stringV = ['alipay_account']
    integerV = ['point', 'money', 'state']
    timeV = ['time']
    foreignKeyV = {'user_id': 'User.id'}


class RequestRecord(Base):
    stringV = ['detail']
    timeV = ['time']
    foreignKeyV = {'user_id': 'User.id'}


class BlackList(Base):
    stringV = ['list']


def init_db():
    Base.metadata.create_all(engine)

    session = DBSession()
    admin1 = Admin(username=ADMIN1_USERNAME, password=ADMIN1_PASSWORD)
    admin2 = Admin(username=ADMIN2_USERNAME, password=ADMIN2_PASSWORD)
    session.add_all([admin1, admin2])

    black_list = BlackList(list=json.dumps([]))
    session.add(black_list)

    session.commit()


def drop_db():
    Base.metadata.drop_all(engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = DBSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

session = DBSession()


def execute(sqls=None):
    from xiaodi.common.tasks import CommonTaskFactory, TaskNames

    return CommonTaskFactory.get_task(TaskNames.EXECUTE_SQL.value).run(sqls)


def start_update_engagement():
    def update_job():
        with DBSession() as session:
            for engagement in session.query(Engagement).all():
                en = json.loads(engagement.engagement)
                en.append(0)
                engagement.engagement = json.dumps(en)
                session.add(engagement)
                session.commit()

    schedule.every().day.at('00:00').do(update_job)


if __name__ == '__main__':
    drop_db()
    init_db()
