# coding=utf-8
import logging
import schedule
from datetime import datetime, timedelta
from functools import wraps

import six
import json
from enum import Enum
from tornado import gen

from xiaodi.api.errors import bad_request_error
from xiaodi.api.errors import forbidden_error
from xiaodi.api.errors import invalid_argument_error
from xiaodi.api.mysql import execute, User, PointRecord
from xiaodi.api.db_utils import get_db_object_by_attr
from xiaodi.api.db_utils import first_award, add_engagement
from xiaodi.settings import AUTO_FINISH_DELAY
from xiaodi.settings import PUBLISH_AWARD, RECEIVE_AWARD
from xiaodi.settings import PUBLISH_ENGAGEMENT, RECEIVE_ENGAGEMENT
from xiaodi.common.const import TASK_LIMIT_DEADLINE
from xiaodi.common.redis_depot import RewardDepot, TaskDepot
from xiaodi.common.utils import tranform_utctime
from xiaodi.common.utils import publish_redis_event, gen_temp_object

LOG = logging.getLogger(__name__)


class DeliveryState(Enum):
    FORCE_DELETE = 0
    AUTO_DELETE = 1
    PUBLISH = 2
    RECEIVE = 3
    SENT = 4
    FINISH = 5


class Operator(Enum):
    DELETE = 'delete'
    RECEIVE = 'receive'
    SENT = 'sent'
    FINISH = 'finish'


def ensure_safe(operator):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            assert len(args) == 2, 'invalid argument for function ensure_safe'

            user, delivery = args
            failed = False
            if operator == Operator.DELETE.value and \
                    (user.id != delivery.puser_id or delivery.state >= DeliveryState.RECEIVE.value):
                failed = True
            elif operator == Operator.RECEIVE.value and \
                    (user.id == delivery.puser_id or delivery.state != DeliveryState.PUBLISH.value):
                failed = True
            elif operator == Operator.SENT.value and \
                    (user.id != delivery.ruser_id or delivery.state != DeliveryState.RECEIVE.value):
                failed = True
            elif operator == Operator.FINISH.value and \
                    (user.id != delivery.puser_id or delivery.state != DeliveryState.SENT.value):
                failed = True

            if failed:
                return bad_request_error('cannot to %s this delivery %d' % (operator, delivery.id))
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class _SyncDeliveryManagerMixin(object):
    @staticmethod
    def delete(user, delivery, session=None):
        if session is None:
            raise ValueError
        if delivery.state == DeliveryState.PUBLISH.value:
            if RewardDepot.exist_reward(user, delivery.id):
                RewardDepot.del_reward(user, delivery.id)
            delivery.state = DeliveryState.AUTO_DELETE.value
            session.add(delivery)
        TaskDepot.del_delete_task(delivery.deadline)

    @staticmethod
    def finish(user, delivery, session=None):
        if session is None:
            raise ValueError
        if delivery.state > DeliveryState.FORCE_DELETE.value and \
                        delivery.state != DeliveryState.FINISH.value:
            RewardDepot.deduct_reward(user, delivery.id)
            point_record1 = PointRecord(
                user_id=user.id,
                type='找人代送',
                balance=user.bright_point + user.original_point,
                number=str(-delivery.reward)
            )
            receiver = session.query(User).filter(User.id==delivery.ruser_id).first()
            # receipt
            receiver.bright_point += delivery.reward
            point_record2 = PointRecord(
                user_id=receiver.id,
                type='帮人代送',
                balance=receiver.bright_point + receiver.original_point,
                number='+' + str(delivery.reward)
            )
            delivery.state = DeliveryState.FINISH.value
            session.add_all([delivery, user, receiver,
                             point_record1, point_record2])
        TaskDepot.del_finish_task(delivery.id)


class _BaseDeliveryManager(object):
    @staticmethod
    def ensure_deadline_in_limit(deadline):
        assert isinstance(deadline, six.string_types), 'deadline is not string'
        try:
            deadline = tranform_utctime(deadline, format='%Y-%m-%d %H:%M')
        except ValueError:
            return invalid_argument_error('invalid deadline format')
        else:
            if (deadline - datetime.now()).days > TASK_LIMIT_DEADLINE:
                return invalid_argument_error('deadline too long, must within 7 days')
        return deadline

    @gen.coroutine
    def _asave(self, delivery):
        yield execute(('add', delivery))
        yield execute(('commit', None))

    @gen.coroutine
    def apublish(self, user, delivery):
        if (yield RewardDepot.aget_available_reward(user)) < delivery.reward:
            raise gen.Return(forbidden_error('no enough money'))

        delivery.state = DeliveryState.PUBLISH.value
        yield self._asave(delivery)

        yield first_award(user, PUBLISH_AWARD)
        yield add_engagement(user, PUBLISH_ENGAGEMENT)
        yield RewardDepot.aset_reward(user, delivery.reward, delivery.id)
        yield TaskDepot.aadd_delete_task(delivery.deadline, delivery.id)
        publish_redis_event("".join(json.dumps([delivery.source.split(u'区')[0], user.id])))

        raise gen.Return(delivery.id)

    @ensure_safe(Operator.DELETE.value)
    @gen.coroutine
    def adelete(self, user, delivery):
        if delivery.state < DeliveryState.RECEIVE.value and \
                (yield RewardDepot.aexist_reward(user, delivery.id)):
            yield RewardDepot.adel_reward(user, delivery.id)
        if delivery.state == DeliveryState.PUBLISH.value:
            yield TaskDepot.adel_delete_task(delivery.deadline)

        delivery.state = DeliveryState.FORCE_DELETE.value
        yield self._asave(delivery)

    @ensure_safe(Operator.RECEIVE.value)
    @gen.coroutine
    def areceive(self, user, delivery):
        delivery.ruser_id = user.id
        delivery.state = DeliveryState.RECEIVE.value
        yield self._asave(delivery)

        yield TaskDepot.adel_delete_task(delivery.deadline)

    @ensure_safe(Operator.SENT.value)
    @gen.coroutine
    def asent(self, user, delivery):
        delivery.state = DeliveryState.SENT.value
        yield self._asave(delivery)

        time_ = datetime.utcnow()+timedelta(days=AUTO_FINISH_DELAY)
        yield TaskDepot.aadd_finish_task(time_, delivery.id)

    @staticmethod
    @ensure_safe(Operator.FINISH.value)
    @gen.coroutine
    def afinish(user, delivery):
        # charge
        yield RewardDepot.adeduct_reward(user, delivery.id)
        point_record1 = PointRecord(
            user_id=user.id,
            type='找人代送',
            balance=user.bright_point + user.original_point,
            number=str(-delivery.reward)
        )
        receiver = yield get_db_object_by_attr(User, id=delivery.ruser_id)
        # receipt
        receiver.bright_point += delivery.reward
        point_record2 = PointRecord(
            user_id=receiver.id,
            type='帮人代送',
            balance=receiver.bright_point + receiver.original_point,
            number='+' + str(delivery.reward)
        )
        delivery.state = DeliveryState.FINISH.value
        yield execute(('add_all', [delivery, user, receiver,
                                   point_record1, point_record2]))
        yield execute(('commit', None))

        yield first_award(user, RECEIVE_AWARD)
        yield add_engagement(user, RECEIVE_ENGAGEMENT)
        yield TaskDepot.adel_finish_task(delivery.id)


class _DeliveryManager(_BaseDeliveryManager, _SyncDeliveryManagerMixin):
    '''include sync method and async method '''


DeliveryManager = _DeliveryManager()


def auto_delete_delivery():
    def delete_job():
        from xiaodi.api.mysql import session_scope, Task

        now = datetime.utcnow()
        for deadline, id_ in TaskDepot.scan_delete_task():
            deadline, id_ = tranform_utctime(deadline), int(id_)
            id_, deadline = int(id_), tranform_utctime(deadline)
            if now < deadline:
                break
            with session_scope() as session:
                delivery = session.query(Task).filter(Task.id == id_).first()
                user = gen_temp_object(id=delivery.puser_id)
                DeliveryManager.delete(user, delivery, session=session)

        LOG.info('auto delete task finished')

    schedule.every(5).minutes.do(delete_job)


def auto_finish_delivery():
    def finish_job():
        from xiaodi.api.mysql import session_scope, Task

        now = datetime.utcnow()
        for id_, deadline in TaskDepot.scan_finish_task():
            deadline, id_ = tranform_utctime(deadline), int(id_)
            if now < deadline:
                break
            with session_scope() as session:
                delivery = session.query(Task).filter(Task.id == id_).first()
                user = gen_temp_object(id=delivery.puser_id)
                DeliveryManager.finish(user, delivery, session=session)

        LOG.info('auto finish task finished')

    schedule.every(30).minutes.do(finish_job)
