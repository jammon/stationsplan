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
- Backup bei ADIT machen; `ssh stationsplan priv/backup-stationsplan.sh && ls -l priv/backup/ `
- hierher kopieren: `scp stationsplan:priv/backup/<...>.json aditbackup.json`
- nach stplan2 kopieren: `scp aditbackup.json stplan2:aditbackup.json`
- Backup von ADIT einlesen: `ssh stplan2 python3.6 stationsplan/manage.py import_from_adit aditbackup.json`


## Ungelöst
- die Admin-Static-Files liegen in (wo?)

