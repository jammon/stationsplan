# Migration zu Uberspace

Uberspace vorbereiten: https://lab.uberspace.de/en/guide_django.html

`pip3.6 install -r stationsplan/requirements.txt --user`
`touch stationsplan/uberspace.wsgi`
`supervisorctl restart uwsgi`

Logs in ~/uwsgi/err.log, ~/logs/supervisord.log

- auf Uberspace `ubermigration` auschecken
- requirements installieren
- Backup von ADIT einlesen
- master auschecken
- neue requirements installieren
- migrieren
- in der Django-Shell alle Wards speichern, damit Ward.json wieder richtig ist (for ward in Ward.objects.all(): ward.save())
- Kontrollieren, ob callshifts korrekt angezeigt werden.