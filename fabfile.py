from __future__ import with_statement
from fabric.api import cd, env, local, run

env.user = 'stplan2'
env.hosts = ['stplan2.uber.space']
code_dir = '~/stationsplan'


def test(verbosity='1', case=''):
    if case:
        local(f"python ./manage.py test {case} "
              f"--settings=stationsplan.settings.dev -v {verbosity}")
    else:
        local("python ./manage.py test sp_app "
              f"--settings=stationsplan.settings.dev -v {verbosity}")


def makemigrations():
    local("python ./manage.py makemigrations sp_app "
          "--settings=stationsplan.settings.dev")


def migrate_local():
    local("python ./manage.py migrate sp_app "
          "--settings=stationsplan.settings.dev")


def serve():
    local("./manage.py runserver --settings=stationsplan.settings.dev")


def sass():
    local("sass sp_app/static/css/main.{scss,css}")
    local("sass sp_app/static/css/print.{scss,css}")


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


def install_requirements():
    run("pip3.6 install -r stationsplan/requirements.txt --user")


def staticfiles():
    with cd(code_dir):
        run("python3.6 manage.py collectstatic --noinput")


def migrate():
    with cd(code_dir):
        run("python3.6 manage.py migrate")


def restart_server():
    run("touch ~/stationsplan/stationsplan/uberspace_wsgi.py")


# call with: `fab deploy:my_branch`
def deploy(branch='master'):
    server_pull(branch)
    install_requirements()
    migrate()
    staticfiles()
    # copy_htaccess()
    # restart_server()
