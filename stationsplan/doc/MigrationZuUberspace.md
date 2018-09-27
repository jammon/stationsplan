# Migration zu Uberspace

- auf Uberspace `ubermigration` auschecken
- requirements installieren
- Backup von ADIT einlesen
- master auschecken
- neue requirements installieren
- migrieren
- in der Django-Shell alle Wards speichern, damit Ward.json wieder richtig ist (for ward in Ward.objects.all(): ward.save())
- Kontrollieren, ob callshifts korrekt angezeigt werden.