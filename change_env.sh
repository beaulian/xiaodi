#!/bin/bash

if [ "$1" = "native" ];then
perl -i -p -e 's/(?<=MONGO_HOST\s=\s")xxx/127.0.0.1/g' settings.py
perl -i -p -e 's/(?<=REDIS_HOST\s=\s")xxx/127.0.0.1/g' settings.py
perl -i -p -e 's/(?<=@)xxx/localhost/g' celery_tasks/celeryconfig.py
elif [ "$1" = "remote" ];then
perl -i -p -e 's/(?<=MONGO_HOST\s=\s")127\.0\.0\.1/xxx/g' settings.py
perl -i -p -e 's/(?<=REDIS_HOST\s=\s")127\.0\.0\.1/xxx/g' settings.py
perl -i -p -e 's/(?<=@)localhost/xxx/g' celery_tasks/celeryconfig.py
fi
