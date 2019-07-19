# Migration zu Uberspace

Uberspace vorbereiten: https://lab.uberspace.de/en/guide_django.html
`ssh stplan2@stplan2.uber.space

`pip3.6 install -r stationsplan/requirements.txt --user`
`touch stationsplan/uberspace.wsgi`
`supervisorctl restart uwsgi`
`python3 ./manage.py migrate`
`python3 ./manage.py test sp_app`

Logs in ~/uwsgi/err.log, ~/logs/supervisord.log

- auf Uberspace `master` auschecken
- requirements installieren
- migrieren
- Backup von ADIT einlesen: `python3 ./manage.py import_from_adit <fixture>`
- in der Django-Shell alle Wards speichern, damit Ward.json wieder richtig ist (for ward in Ward.objects.all(): ward.save())
- Kontrollieren, ob callshifts korrekt angezeigt werden.

## Ungelöst
- die Admin-Static-Files liegen in (wo?)

