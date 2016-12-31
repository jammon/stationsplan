# Stationsplan

- Monatsdarstellung für Stationen und Mitarbeiter
- neuen Monat anfügen
- Stationen und Mitarbeiter eingeben:
    + Station: Name, Kurzname, Stellen
    + Mitarbeiter: Name, Kürzel
- Wenn ein Feld bei den Stationen ausgefüllt wird:
    + soll der Rest des Monats dem MA zugeordnet werden,
    + sollen die Felder der MA aktualisiert werden.

Ein Tag kann für jede Stelle einen Mitarbeiter haben. Er hält nach, an welchen Stellen der MA eingeplant ist.

Mitarbeiter, die gestern Dienst hatten oder im Urlaub sind, dürfen nicht verplant werden.

## Krankenhaus
Ein Krankenhaus hat verschiedene *Abteilungen*. Jede Abteilung hat mehrere *Stationen*, *Dienste* oder *Funktionen*. Diese müssen mit einer oder mehreren *Personen* besetzt werden. Personen können auch im *Urlaub/Fortbildung/Frei* oder *krank* sein und so nicht für die Planung zur Verfügung stehen.
Jede Person gehört zu einer Abteilung. Stationen, Dienste oder Funktionen können auch von mehreren Abteilungen besetzt werden.

## User
Angemeldete User können verschiedene Stufen von Benutzerrrechten haben. Sie können:
- eine Planung ansehen, - Viewer
- die Planung von verschiedenen Stationen bearbeiten, - Editor
- Benutzer anlegen, bearbeiten oder löschen, - Department Leader
- Stationen und Personen anlegen, bearbeiten oder löschen, - Department Leader
- für mehrere Abteilungen (einer Klinik) Administratorfunktionen wahrnehmen. - Company Admins

### Viewer
Haben keine Berechtigungen, können nur ansehen.

### Editor
Können Planungen der eigenen Abteilung ändern.

### Department Leader
Können Benutzer (Viewer, Editor, Department Leader) für die eigene Abteilung anlegen/bearbeiten.
Können Stationen und Personen für die eigene Abteilung anlegen/bearbeiten.

### Company Admins
Können Departments anlegen/bearbeiten.
Können alles was Department Leader können auf Company-Ebene.

## Backend
- Der Monat soll gespeichert werden, wenn er erstellt ist
- Wenn eine Besetzung geändert wurde, soll das gespeichert werden.
- Wenn man sich anmeldet, soll der aktuelle Plan geladen werden.
- Wenn man "nächsten Monat" klickt, soll der erstellt oder geladen werden.
- Man soll die Personen bearbeiten können
- Man soll die Stationen/Dienst bearbeiten können
- Wenn Urlaub oder Krank eingetragen wird, sollen die bisherigen Verpflichtungen nach dem Urlaub weiterlaufen.

- Funktionen (=Stationen) können durchlaufen (Stationsversorgung, Urlaub) oder nicht (Nachtdienst, Tagdienst)
- Bei Urlaub oder Krank behält die Person ihre Funktionen, sie werden aber für diesen Tag nicht angezeigt.
- Bei Nachtdienst werden für diesen Tag alle anderen Funktionen nicht angezeigt, für den Folgetag nur die dazu Passenden (wieder Nachtdienst), die anderen nicht.
- Ablauf:
    + When on_leave or yesterdays nightshift is added: the person is unavailable for all staffings of the day.
    + When yesterdays ward with reduced availability for the next day is added: the person is unavailable for all non-fitting staffings of the day.
    + When on_leave or yesterdays nightshift or yesterdays ward with reduced availability for the next day is removed: the availability of the person must be calculated newly.

## Stationsplan nach uberspace umziehen
- Auf jammon@lynx.uberspace.de ist die Django-App in ~/projects/stationsplan.
- Als Domain wird zuerst stationsplan.jammon.lynx.uberspace.de (=DJANGOURL) benutzt.
- die Admin-Static-Filea liegen in /var/www/virtual/$USER/$DJANGOURL/static/

## Planungen mit Anfang und Ende eingeben
Wenn man eine Planung eingibt, die ein oder mehrere bisherige Planungen überdeckt, sollen diese verlinkt und als inaktiv markiert werden. So ist ein Undo möglich.

Wenn eine neue Planung eine alte teilweise überlappt, wird sie so beschnitten, dass sie direkt anschließt und nicht mehr überlappt. (Nach dem bisherigen UI kann die neue Planung nur mit ihrem Ende den Anfang einer alten Planung überdecken.)

Wenn ein Change mit add=False und angegebenem Ende andere Planungen überdeckt, werden diese gekürzt oder gelöscht.