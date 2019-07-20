# Migration zu Uberspace

Uberspace vorbereiten: https://lab.uberspace.de/en/guide_django.html
`ssh stplan2@stplan2.uber.space

Logs in ~/uwsgi/err.log, ~/logs/supervisord.log

`fab deploy master` macht:
- auf Uberspace `master` auschecken
- requirements installieren
- migrieren
- Staticfiles sammeln (`collectstatic`)

Dann:
- Backup von ADIT einlesen: `python3 ./manage.py import_from_adit <fixture>`
- `weekdays` im Visitendienst setzen
- in der Django-Shell alle Wards speichern, damit Ward.json wieder richtig ist (for ward in Ward.objects.all(): ward.save())
- Kontrollieren, ob callshifts korrekt angezeigt werden.

## Ungelöst
- die Admin-Static-Files liegen in (wo?)

