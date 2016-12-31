from __future__ import with_statement
from fabric.api import cd, env, local, run

env.user = 'stationsplan'
env.hosts = ['stationsplan.de']
code_dir = '~/priv/stationsplan'


def test():
    local("./manage.py test sp_app")


def serve():
    local("./manage.py runserver")


def sass():
    local("sass sp_app/static/css/main.{scss,css}")


def commit():
    local("git add -p && git commit")


def push():
    local("git push")


def prepare_deploy():
    test()
    commit()
    push()


# call with: `fab server_pull:my_branch`
def server_pull(branch='master'):
    with cd(code_dir):
        run("git pull origin " + branch)


def staticfiles():
    with cd(code_dir):
        run("source ~/priv/venv/bin/activate && ./manage.py "
            "collectstatic --noinput")


def migrate():
    with cd(code_dir):
        run("source ~/priv/venv/bin/activate && ./manage.py migrate")


def copy_htaccess():
    run('cp ~/priv/stationsplan/htaccess ~/htdocs/.htaccess')


def restart_server():
    run("touch ~/htdocs/app.wsgi")


# call with: `fab deploy:my_branch`
def deploy(branch='master'):
    server_pull(branch)
    staticfiles()
    migrate()
    copy_htaccess()
    restart_server()
