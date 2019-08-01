# Testing

Folgende Funktionen muss das Programm können:
## Anmeldung
- Anmelden als einfacher User ("kim1")
    + sieht `Stationen`, `Dienste`, `Heute`
    + sieht nicht `Funktionen`
    + sieht im Settings-Menü `Abmelden` aber nicht `Passwort ändern`
    + `Stationen`:
        * kann Zeitraum weiterschalten
        * Klick auf die Titelzeile mit dem Tag zeigt die Seite `Heute`
        * Klick auf `Aufgaben` zeigt die Aufgaben
        * kein Approval möglich (Klick auf Station in `Stationen`)
        * keine Bearbeitung möglich (Klick auf geplante Personen)
    + `Dienste`:
        * kann Zeitraum weiterschalten
        * keine Bearbeitung möglich (Klick auf geplante Personen)
    + `Heute`:
        * Nur Anschauen, keine Interaktion
- Anmelden als Editor ("kim1editor")
- Anmelden als Department Leader ("?")
