# Currently not working
# ssh stationsplan python3.6 stationsplan/manage.py dumpdata --output current_data.json --exclude sessions --exclude auth.permission --exclude contenttypes 
# scp stationsplan:current_data.json current_data.json
# ssh stationsplan rm current_data.json
# python3.6 manage.py flush --noinput
# python3.6 manage.py loaddata current_data.json