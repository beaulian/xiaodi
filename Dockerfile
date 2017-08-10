FROM daocloud.io/shenaishiren/xiaodi-final:api-fcd0fed

# set image owner
MAINTAINER Jiawen Guan <gjw.jesus@qq.com>

VOLUME /var/log/xiaodi

# expose port
EXPOSE 8001
EXPOSE 8002
EXPOSE 8003
EXPOSE 8004

WORKDIR /code

ADD . /code

ENV TZ=Asia/Shanghai

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN cp conf/*.conf /etc/supervisor/conf.d/

CMD cron && /usr/bin/supervisord -n
