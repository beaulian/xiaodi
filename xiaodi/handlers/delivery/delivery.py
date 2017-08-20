# coding=utf-8
from datetime import datetime
from tornado import gen
from delivery_utils import DeliveryManager
from xiaodi.api.mysql import Task, execute, User
from xiaodi.common.image_handler import save_image_to_oss
from xiaodi.settings import OSS_THUMBNAIL_PATH, DEFAULT_THUMBNAIL
from xiaodi.settings import MAX_DELIVERY_PER_PAGE, ORDER_FIELDS


@gen.coroutine
def publish_delivery(user, source=None, destination=None, reward=None,
                     type=None, weight=None, thumbnail=None,
                     contact=None, deadline=None, describe=None):
    deadline = DeliveryManager.ensure_deadline_in_limit(deadline)
    if thumbnail:
        image_path = yield save_image_to_oss(thumbnail, OSS_THUMBNAIL_PATH,
                                             str(datetime.now()),
                                             when_fail=DEFAULT_THUMBNAIL.format(type=type))
    else:
        image_path = DEFAULT_THUMBNAIL.format(type=type)

    delivery = Task(
        puser_id=user.id,
        ruser_id=user.id,
        source=source,
        destination=destination,
        reward=reward,
        type=type,
        weight=weight,
        thumbnail=image_path,
        contact=contact,
        deadline=deadline,
        describe=describe,
        school=user.school
    )
    delivery_id = yield DeliveryManager.apublish(user, delivery)

    raise gen.Return(delivery_id)


@gen.coroutine
def get_delivery(school=None, sort=None, ascend=None,
                 keyword=None, page_num=None):
    from sqlalchemy import and_, or_

    order_way = getattr(Task, ORDER_FIELDS[sort])
    if not ascend:
        order_way = order_way.desc()

    if keyword:
        keyword = ['%{}%'.format(k) for k in keyword.encode('utf-8').split()]
        task_fields = ['source', 'type', 'destination']
        task_list = [and_(getattr(Task, attr).like(k)
                     for k in keyword) for attr in task_fields]
        user_fields = ['nickname', 'campus', 'hostel']
        user_list = [and_(getattr(User, attr).like(k)
                     for k in keyword) for attr in user_fields]
        deliveries = yield execute(sqls=[
            ('query', Task),
            ('join', (User, Task.puser_id == User.id)),
            ('filter', Task.school == school),
            ('filter', or_(*(task_list + user_list))),
            ('order_by', order_way),
            ('offset', (page_num - 1) * MAX_DELIVERY_PER_PAGE),
            ('limit', MAX_DELIVERY_PER_PAGE),
            ('all', None)
        ])
    else:
        deliveries = yield execute(sqls=[
            ('query', Task),
            ('filter', Task.school == school),
            ('order_by', order_way),
            ('offset', (page_num - 1) * MAX_DELIVERY_PER_PAGE),
            ('limit', MAX_DELIVERY_PER_PAGE),
            ('all', None)
        ])

    raise gen.Return([delivery.to_json() for delivery in deliveries])
