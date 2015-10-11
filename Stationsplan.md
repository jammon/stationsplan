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
- eine Planung ansehen,
- die Planung von verschiedenen Stationen bearbeiten,
- Benutzer anlegen, bearbeiten oder löschen,
- Stationen und Personen anlegen, bearbeiten oder löschen,
- für mehrere Abteilungen (einer Klinik) Administratorfunktionen wahrnehmen.

## Backend
- Der Monat soll gespeichert werden, wenn er erstellt ist
- Wenn eine Besetzung geändert wurde, soll das gespeichert werden.
- Wenn man sich anmeldet, soll der aktuelle Plan geladen werden.
- Wenn man "nächsten Monat" klickt, soll der erstellt oder geladen werden.
- Man soll die Personen bearbeiten können
- Man soll die Stationen/Dienst bearbeiten können

## Done
- Es soll in /plan immer das Department des Users dargestellt werden
- in /monat sollen die Changes aus dem Department des Users übermittelt werden.
- login und logout implementieren
- Jeder User muss ein Department haben
- im "Nächsten Monat" sollen nur die Personen dargestellt werden, die dann noch tätig sind.

## TODO
- Reihenfolge der Stationen vorgeben
- Wie sollen neue User angelegt werden? Admins könnten die User für das eigene Department anlegen
