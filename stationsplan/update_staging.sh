# Which commit is production on?
commit=`ssh production 'cd stationsplan; git log -1'| awk '/^commit/ {print $2}'`
# Dump production data
filename=`date +%Y%m%d`.json.gz
ssh production "cd stationsplan; python3.6 manage.py dumpdata --settings=stationsplan.settings.uberspace --exclude=auth.Group --exclude=auth.Permission --exclude=contenttypes --exclude=admin | gzip > $filename"
# copy data from production to staging
scp production:stationsplan/"$filename" .
scp "$filename" staging:stationsplan/
# delete database on staging
ssh staging ./delete-database.sh
# checkout old commit on staging, migrate
ssh staging "cd stationsplan; git checkout $commit"
# migrate
ssh staging "cd stationsplan; python3.9 manage.py migrate --settings=stationsplan.settings.uberspace"
# load data to staging
ssh staging "cd stationsplan; gunzip $filename; python3.9 manage.py loaddata --settings=stationsplan.settings.uberspace `date +%Y%m%d`.json"
# checkout master on staging, migrate
ssh staging "cd stationsplan; git checkout master; python3.9 manage.py migrate"
