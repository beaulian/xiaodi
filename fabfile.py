# -*- coding: utf-8 -*-

from fabric.api import cd, run, local, env
from fabric.contrib.files import exists

code_path = "/root/product/xiaodi/xiaodi-api/"
code_dir = "/root/product/xiaodi/xiaodi-api/xiaodi"


def remote_pull():
    with cd(code_dir):
        run("git pull")

def local_pull():
    local("git pull")

def dynamic_reload():
    with cd(code_dir):
        run("git pull")
        run("docker-compose build")
        run("docker exec xiaodi_api_1 rm /code/xiaodi/celery_tasks/celerybeat.pid")
        run("supervisorctl restart xiaodi_api")


def static_reload():
    with cd(code_dir):
        run("git pull")
