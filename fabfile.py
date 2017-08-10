# -*- coding: utf-8 -*-

from fabric.api import cd, run, local, env
from fabric.contrib.files import exists

code_path = "xxxx"
code_dir = "xxxx"


def remote_pull():
    with cd(code_dir):
        run("git pull")


def local_pull():
    local("git pull")


def dynamic_reload():
    with cd(code_dir):
        run("git pull")
        run("docker-compose build")
        run("docker exec xiaodi_api_1 rm /xxx/celerybeat.pid")
        run("supervisorctl restart xiaodi_api")


def static_reload():
    with cd(code_dir):
        run("git pull")
