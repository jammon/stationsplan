from __future__ import with_statement
from fabric.api import cd, env, local, run

env.user = 'stationsplan'
env.hosts = ['stationsplan.de']
code_dir = '~/priv/stationsplan'


def test():
    local("./manage.py test sp_app")


def commit():
    local("git add -p && git commit")


def push():
    local("git push")


def prepare_deploy():
    test()
    commit()
    push()


def server_pull():
    with cd(code_dir):
        run("git pull origin master")


def staticfiles():
    with cd(code_dir):
        run("./manage.py collectstatic")
