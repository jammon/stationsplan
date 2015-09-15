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

## Backend
- Der Monat soll gespeichert werden, wenn er erstellt ist
- Wenn eine Besetzung geändert wurde, soll das gespeichert werden.
- Wenn man sich anmeldet, soll der aktuelle Plan geladen werden.
- Wenn man "nächsten Monat" klickt, soll der erstellt oder geladen werden.
- Man soll die Personen bearbeiten können
- Man soll die Stationen/Dienst bearbeiten können

## TODO
- Es sollen nur die Ärzte in der Tabelle erscheinen, die in dem Monat in der Klinik arbeiten.
- Es sollen nur die Ärzte in der Auswahl erscheinen, die in dem Monat in der Klinik arbeiten.
- In der Titelzeile auch die Wochentage anzeigen.
