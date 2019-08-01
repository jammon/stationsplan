ssh stplan2@stplan2.uber.space python3.6 stationsplan/manage.py dumpdata --output current_data.json --exclude sessions 
scp stplan2@stplan2.uber.space:current_data.json current_data.json
ssh stplan2@stplan2.uber.space rm current_data.json
python3.6 manage.py flush --noinput
python3.6 manage.py loaddata current_data.json