# Stationsplan

## Krankenhaus
Ein Krankenhaus hat verschiedene *Abteilungen*. Jede Abteilung hat mehrere *Stationen*, *Dienste* oder *Funktionen*. Diese müssen mit einer oder mehreren *Personen* besetzt werden. Personen können auch im *Urlaub/Fortbildung/Frei* oder *krank* sein und so nicht für die Planung zur Verfügung stehen.
Jede Person gehört zu einer Abteilung. Stationen, Dienste oder Funktionen können auch von mehreren Abteilungen besetzt werden.

## User
Angemeldete User können verschiedene Stufen von Benutzerrrechten haben. 
- **Viewer**: können eine Planung ansehen.
- **Editor**: können die Planung von verschiedenen Stationen bearbeiten. (Haben die Permission `sp_app.is_editor`.)
- **Department Leader**: können Benutzer, Stationen und Personen für die eigene Abteilung anlegen, bearbeiten oder löschen. (Haben die Permission `sp_app.is_dep_lead`.)
- **Company Admins**: können Benutzer (Viewer, Editor, Department Leader), Stationen und Personen für alle Abteilungen anlegen/bearbeiten. (Haben die Permission `sp_app.is_company_admin`.)

Die genannten Permissions werden in der Session gespeichert.
Alle außer Viewer können ihr Passwort ändern und ihre Sessions laufen mit dem Schließen des Browsers ab.


## Change(Logging) vs. Planning
Ein *Change* wird vom Nutzer eingegeben, auf dem Server mit den anderen Planungen abgeglichen und dann zurückgegeben und ins UI eingearbeitet.
Ein *Planning* ist das Ergebnis der konsolidierten Changes, das initial beim Aufruf der Seite übergeben wird.

Wenn die Seite aufgerufen wird,
- `main.initialize_site`: initialisiert alle Variablen, dann
    - `models.start_day_chain`: initialisiert nur den ersten Tag
    - ruft über Backbone.history.start die View auf
- die View ruft über Umwege `models.get_period_days` auf
- hier werden die Tage über `days.get_day` initialisiert.

## Planungen mit Anfang und Ende eingeben
Wenn man einen Change eingibt, der ein oder mehrere bisherige Planungen überdeckt, sollen diese verlinkt und als inaktiv markiert werden. So ist ein Undo möglich.

Wenn ein neuer Change eine alte Planung teilweise überlappt, wird sie so beschnitten, dass sie direkt anschließt und nicht mehr überlappt.

Wenn ein Change mit add=False und angegebenem Ende andere Planungen überdeckt, werden diese gekürzt oder gelöscht.

## Finalisierte Planungen
- Für Wards kann ein Datum angegeben werden, bis zu dem Planungen sichtbar sind.
- Default ist None.
- Alle Planungen nach diesem Datum sind nur für Editoren sichtbar.
- Für die Anderen enden die Planungen an diesem Datum.

## Für das Handbuch
- Anonyme Personen sollten nicht für "Krank" oder "Frei" buchbar gemacht werden.

## Export nach CalDAV
- bei der Freigabe sollen die Planungen für bestimmte Wards in einen CalDAV-Server gespeichert werden.
- Nach Wunsch bekommen die betroffenen Personen dann eine Mail.
- für jede Person gibt es einen Principal.
- Wenn Dienste in einem freigegebenen Ward geändert werden, werden diese für eine Benachrichtigung vorgemerkt. Der Editor kann dann die Personen über die Änderungen mit einem Kommentar per Mail benachrichtigen.

## Feiertage
Feiertage werden berechnet.

### Feiertage an festen Terminen
- 01.01.: Neujahr
- 06.01.: Heilige Drei Könige
- 08.03.: Frauentag
- 01.05.: Maifeiertag
- 08.08.: Augsburger Hohes Friedensfest
- 15.08.: Mariä Himmelfahrt
- 20.09.: Weltkindertag
- 03.10.: Tag der Deutschen Einheit
- 31.10.: Reformationstag
- 01.11.: Allerheiligen
- 25.12.: 1. Weihnachtstag
- 26.12.: 2. Weihnachtstag

### Abhängig von Ostern:
- Rosenmontag -48
- Karfreitag: -2
- Ostermontag: +1
- Christi Himmelfahrt: +39
- Pfingstmontag: +50
- Fronleichnam: +60

Ostertermine
2017 - 16.04.
2018 - 1.04.
2019 - 21.04.
2020 - 12.04.
2021 - 4.04.
2022 - 17.04.
2023 - 9.04.
2024 - 31.03.
2025 - 20.04.
2026 - 5.04.
2027 - 28.03.
2028 - 16.04.
2029 - 1.04.
2030 - 21.04.

Buß- und Bettag: Mittwoch vor dem 23.11.

Jedes Krankenhaus gehört zu einer Region, die die Feiertage definiert. Sollte ein Krankenhaus zusätzliche Feiertage haben, muss dafür eine neue Region definiert werden.

## Tabelle an Screengröße anpassen
### Tabellenbreite
- Bei Screengröße 'lg' 1 Monat
- Bei Screengröße 'md' 4 Wochen
- Bei Screengröße 'sm' 3 Wochen
- Bei Screengröße 'xs' und window-width>550 2 Wochen
- Bei Screengröße 'xs' und window-width<=550 1 Woche

### Pfad
- `/plan/YYYYMM` zeigt bei Monatsansicht den Monat, bei Zeitraumansicht beginnt der Zeitraum mit dem Montag der Woche, in der der Monatserste liegt.
- `/plan/YYYYMMDD` zeigt bei Monatsansicht den Monat des Tages (wie bei `YYYYMM`), bei Zeitraumansicht beginnt der Zeitraum mit dem Montag der Woche, in der der Tag liegt.

D.h. `/plan/YYYYMM` ist äquivalent zu `/plan/YYYYMM01`.

### Screengröße abfragen
    <div class='device-check visible-xs' data-device='xs'></div>
    <div class='device-check visible-sm' data-device='sm'></div>
    <div class='device-check visible-md' data-device='md'></div>
    <div class='device-check visible-lg' data-device='lg'></div>

you can then find the current grid option with:

    function get_current_grid_option(){
        return $('.device-check:visible').attr('data-device')
    }

## Plan regelmäßig aktualisieren
- '/plan' liefert die Zeit seit der letzten Änderung mit, 
- jede Änderung gibt ihre pk mit,
- der Server meldet die Zeit nach der letzten Änderung
- nach einer Zeit, die von last_change abhängt, wird ein Update abgeholt
- dafür wird die letzte bekannte pk angegeben
- beim Update werden die neuesten Änderungen seit der letzten bekannten pk geliefert
- beim Speichern von changes wird ebenfalls die letzte bekannte pk mitgegeben.
- zurückgeliefert werden dann die neuestens changes inklusive der gerade gespeicherten (wenn sie erfolgreich war).

## "Id" von Personen und Funktionen (Ward)
- Auf Serverseite ist die Id die numerische pk. 
- In der Verarbeitung im Client werden die Personen/Wards nach ihrem shortname indiziert.
- Vom Server werden Personen/Wards mit Id und Shortname geschickt.
- ChangeLoggings werden vom Server geliefert in `ajax.updates` und als Antwort in `ajax.changes`. Sie enthalten die Shortnames von Personen/Wards.
- Plannings werden vom Server geliefert in `views.plan`. Sie enthalten die Ids von Personen/Wards.
- Changes werden vom Client an der Server in `changes` geschickt. Sie enthalten die Ids.

## Verwaltung von Personen und Funktionen für Nutzer
- Personen
    + Neue Person eingeben
    + Person bearbeiten
    + Person soll vorübergehend nicht planbar sein (Rotation, Elternzeit, Forschungsaufenthalt)
- Funktionen
    + Neue Funktion eingeben
    + Funktion bearbeiten
- Personen einer Funktion zuordnen √

## Was Nutzer nicht bearbeiten können
- Feiertage
- Company
- Abteilung
- Bearbeiter (Employee)

## Auswahl der Abteilung
- Wenn ein Editor mehr als eine Abteilung bearbeiten kann, soll er auf die anderen Abteilungen umschalten können.
- Bei Krank/Urlaub sollen nur die MA der aktuellen Abteilung angezeigt werden.

## Going public
- Dokumentation schreiben
- Personen und Funktionen mit htmx bearbeiten √
- Einstieg für neue Kliniken anbieten
    - Company Admin anlegen
        + Neuer User gibt Name, Email und Passwort ein
        + User wird als active=False angelegt
        + Mail an User mit token geht raus, Zeitlimit 24 h
        + Aufruf der Bestätigungsurl aktiviert den Account
    - Klinikname und Region eingeben
    - Abteilungen anlegen
    - User anlegen
        + User ohne Rechte
        + (weitere Editoren)
    - Funktionen anlegen
    - Personen anlegen Übersicht
- iCal-Anbindung
- Erste drei Monate frei, erst dann bezahlen
- Wildcard Certificate installieren
    + Jede Klinik bekommt eine Domain mit ihrem Kurznamen
    + Bisherige Kliniken können sich noch an `stationsplan.de` anmelden
- Design überarbeiten
- Beispielklinik anlegen
    + Namen: Huber, Krüger, Strey, Voigtländer, Beyerlein, Theis, Zaremba, Dornig, Zawadzki, Böhmer, Schneider, Krause, Gutschow, Karout, Avci, Abele.
    
### Werbung, Aussagen über Funktion und Leistung
- Die Planung ist erreichbar unter `kurzname.stationsplan.de`
- Die Pläne sind nur nach Anmeldung sichtbar
- Nur berechtigte Personen können verändern
- Pläne sind von überall einsehbar
- Keine unbesetzten Positionen, keine versehentlich doppelte Verplanung
- Import in die Kalenderfunktion von Smartphones

## Umstellung auf htmx
- if they left the company, they cannot be planned
- a vacation can be planned for the members of the current department
- is she/he on leave?
- Is this ward in their portfolio?
- the person is not anonymous
    - does yesterdays planning allow this?
        - if they were not on leave yesterday ...
        - check if yesterdays plannings prohibit this
    - does todays planning allow this?

## iCal-Anbindung
- django_ical für den Feed
- Event ist Planning 
- Für jede Person wird eine URL erstellt, unter der die Dienst abonniert wereden können. Diese wird an die Mailadresse geschickt. Es kann auch eine neue URL erstellt werden. Wenn die neue URL benutzt wird, wird die alte ungültig.
- Neue Planungen müssen für den Feed erst aktiv freigegeben werden
    + Es soll angezeigt werden, wenn es nicht freigegebene Planungen gibt
- Für jede Funktion kann festgelegt werden, ob sie im Feed auftaucht
- Sortierung des ical-Feeds?
- Last-Modified-Header in Feed setzen

### Regeldienst und Sonderaufgaben
Es sollen Funktionen als regulärer Dienst definiert werden können (z.B. Stationsarbeit) und andere, die einen aus dem Regeldienst raus nehmen (z.B. NEF, Funktionsdienst, OP o.ä.)
> Dies geschieht mit ward.not_with_this
