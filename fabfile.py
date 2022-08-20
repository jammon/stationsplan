from __future__ import with_statement
from fabric.api import cd, env, local, run

env.user = "stplan2"
env.hosts = ["stplan2.uber.space"]
code_dir = "~/stationsplan"


def test(verbosity="1", case=""):
    local(f"pytest {case}")


def makemigrations():
    local(
        "python ./manage.py makemigrations sp_app "
        "--settings=stationsplan.settings"
    )


def migrate_local():
    local("python ./manage.py migrate sp_app --settings=stationsplan.settings")


def serve():
    local("./manage.py runserver --settings=stationsplan.settings")


def sass():
    local("sass sp_app/static/css/main.{scss,css}")
    local("sass sp_app/static/css/print.{scss,css}")


def makemessages():
    local("./manage.py makemessages -l de -i venv")


def compilemessages():
    local("./manage.py compilemessages")


# call with: `fab server_pull:my_branch`
def server_pull(branch="master"):
    with cd(code_dir):
        run("git pull origin " + branch)


def install_requirements():
    run("pip3.9 install -r stationsplan/requirements.txt --user")


def staticfiles():
    with cd(code_dir):
        run("python3.9 manage.py collectstatic --noinput")


def migrate():
    with cd(code_dir):
        run("python3.9 manage.py migrate")


def restart_server():
    run("touch ~/stationsplan/stationsplan/uberspace_wsgi.py")


# call with: `fab deploy:my_branch`
def deploy(branch="master"):
    server_pull(branch)
    install_requirements()
    migrate()
    staticfiles()
    # copy_htaccess()
    # restart_server()


def backup():
    run(
        "mysqldump stplan2 | xz > "
        '~/backup/stationsplan-`date +"%Y-%m-%d-%H-%M-%S"`.sql.xz'
    )
