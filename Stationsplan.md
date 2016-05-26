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

## TODO
- Wie sollen neue User angelegt werden? Admins könnten die User für das eigene Department anlegen
- Nur finalisierte Planungen sind für Benutzer ohne besondere Berechtigung sichtbar.
- Single page app schreiben
    + Angemeldete Nutzer sollen gleich nach /plan kommen.
    + Unter "/" sollte man entweder den Begrüßungsbildschirm oder den Plan sehen, je nach Anmeldestatus.
    + View für nur die Dienste
    + Es sollen immer alle Changes geladen werden, die Monate werden erstellt und nach Bedarf angezeigt.
    + Changes für abgelaufene Monate werden konsolidiert als Ausgangspunkt für die Planung.
    + Abgelaufene Monate werden als Plan bzw. HTML gespeichert.
- Customize the default error views 
- Der Kurzname einer Funktion sollte kein Komma enthalten.
- Logging anzeigen
- Wochenendtage mit stärkerem Rand
- Auch Ärzte von Fremdabteilungen sollen angezeigt werden, wenn sie in den angezeigten Funktionen Dienst tun. Sollen dann nicht bearbeitbar sein.
- Kommentare an Änderungen anhängen
- Kommentare oder Nachrichten unabhängig von Änderungen
- Dienstwünsche eingeben, für jede Person müsste ein User erstellt werden (z.B. 'amm-bot')
- Markierung für fehlende Personen fixen
- wann ist collection.no_staffing und wann ist collection===undefined?
- Ward.continued sollte rein deklarativ sein und keine Auswirkung auf das Verhalten haben.

## Done
- Es soll in /plan immer das Department des Users dargestellt werden
- in /monat sollen die Changes aus dem Department des Users übermittelt werden.
- login und logout implementieren
- Jeder User muss ein Department haben
- im "Nächsten Monat" sollen nur die Personen dargestellt werden, die dann noch tätig sind.
- Logging einrichten
    + Jede Besetzungsänderung soll ein Logging folgender Art auslösen: "$User: $Person ist ab/am $Datum für $Station [nicht mehr] eingeteilt" oder 
- Personen können nur bestimmte Funktionen ausüben
- Reihenfolge der Stationen vorgeben
- In admin sollten nur die Personen/Wards angeboten werden, die zur eigenen Abteilung gehören
- In Person/Ward sollte die eigene Abteilung/Company bei der Auswahl bzw. beim Hinzufügen vorbelegt sein.
- Berechtigungen implementieren
- Abfragen auf die Departments einschränken
- Wenn jemand für 'krank' oder 'Urlaub' eingetragen wird, bleiden die Duties vorhanden, er ist aber nicht für die Stationen eingetragen?
- Man soll festlegen können, dass nach einem Dienst nur bestimmte Funktionen ausgeübt werden können.
- Meldungen für noscript und loading
- Wenn man eine frühere Planung beendet, wurde dadurch eine spätere Planung unsichtbar (fixed in 06b164179c7bc08c202859ad2db515e09e4bc4d4)
- Das "dataset"-Attribut ist im IE10 nicht implementiert.
- im ChangeStaffView soll mehr als eine Veränderung gemacht werden können und angegeben werden können, ob diese für einen oder viele Tage gelten soll.
