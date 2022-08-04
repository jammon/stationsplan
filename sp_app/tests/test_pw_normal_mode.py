from time import sleep
from playwright.sync_api import Playwright, sync_playwright, expect

SERVER = "http://localhost:8000/"
WAIT = 0.3


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    def anmelden(username):
        page.goto(SERVER)
        page.locator("#username").fill(username)
        page.locator("#password").fill("123456")
        page.locator("#password").press("Enter")

    def abmelden():
        page.locator(".glyphicon-cog").click()
        page.locator("text=Abmelden").click()

    def tools_inhalt(items, not_items=[]):
        page.locator(".glyphicon-cog").click()
        expect(page.locator(".dropdown-menu")).to_contain_text(items)
        for i in not_items:
            expect(page.locator(".dropdown-menu")).not_to_contain_text(i)
        page.locator(".glyphicon-cog").click()

    def edit_dept(dept):
        page.goto(SERVER + "setup/")
        page.locator(f"text={dept}").click()
        sleep(WAIT)
        page.locator('input[name="name"]').fill("Neuer Name")
        page.locator('input[name="name"]').press("Enter")
        sleep(WAIT)
        page.locator("text=Neuer Name").click()
        page.locator('input[name="name"]').fill(dept)
        sleep(WAIT)
        page.locator('input[name="name"]').press("Enter")
        sleep(WAIT)

    # Anmelden mit den verschiedenen Berechtigungs-Levels
    # - Welche Setup-Optionen werden gezeigt?
    # - Abteilung verändern
    # - Employee bearbeiten
    # - Person bearbeiten
    # - Funktion bearbeiten

    # is_company_admin
    anmelden("_pwt2_is_company_admin")
    tools_inhalt(
        ["Abmelden", "Passwort ändern", "Einstellungen"], ["Admin-Seite"]
    )
    page.goto(SERVER + "setup/")
    expect(page.locator("#setup-nav")).to_contain_text(
        [
            "Abteilungen",
            "Bearbeiter/innen",
            "Mitarbeiter/innen",
            "Funktionen",
            "Zuordnung",
        ]
    )
    edit_dept("Innere")
    edit_dept("Chirurgie")
    # Persons
    page.locator("text=Mitarbeiter/innen").click()
    sleep(WAIT)
    expect(page.locator("#setup-tab")).to_contain_text(
        ["Person A", "Person B", "Chirurg"]
    )
    page.locator("text=Funktionen").click()
    sleep(WAIT)
    expect(page.locator("#setup-tab")).to_contain_text(["Ward A", "Ward B"])
    abmelden()

    # is_dep_lead
    anmelden("_pwt2_is_dep_lead")
    tools_inhalt(
        items=["Abmelden", "Passwort ändern", "Einstellungen"],
        not_items=["Admin-Seite"],
    )
    page.goto(SERVER + "setup/")
    expect(page.locator("#setup-nav")).to_contain_text(
        [
            "Bearbeiter/innen",
            "Mitarbeiter/innen",
            "Funktionen",
            "Zuordnung",
        ]
    )
    expect(page.locator("#setup-nav")).not_to_contain_text("Abteilungen")
    # Persons
    page.locator("text=Mitarbeiter/innen").click()
    sleep(WAIT)
    expect(page.locator("#setup-tab")).to_contain_text(
        ["Person A", "Person B"]
    )
    expect(page.locator("#setup-tab")).not_to_contain_text("Chirurg")
    page.locator("text=Funktionen").click()
    sleep(WAIT)
    expect(page.locator("#setup-tab")).to_contain_text(["Ward A", "Ward B"])
    abmelden()

    # is_editor
    anmelden("_pwt2_is_editor")
    tools_inhalt(
        ["Abmelden", "Passwort ändern"], ["Einstellungen", "Admin-Seite"]
    )
    abmelden()

    # nur Lese-Berechtigung
    anmelden("_pwt2_None")
    tools_inhalt(
        ["Abmelden"], ["Passwort ändern", "Einstellungen", "Admin-Seite"]
    )
    abmelden()

    # page.locator("text=Bearbeiter/innen").click()
    # page.locator('p:has-text("_pwt2_None (Lesen)")').click()
    # page.locator("text=Mitarbeiter/innen").click()
    # page.locator("text=Funktionen").click()
    # page.locator("text=Zuordnung").click()
    # page.locator("text=Bearbeiter/innen").click()
    # page.locator("text=_pwt2_is_dep_lead (Abteilungsleiter/in)").click()
    # page.locator('text=Innere (Inn) >> input[name="departments"]').check()
    # page.locator("text=Speichern").click()
    # page.locator("text=_pwt2_is_company_admin (Admin)").click()
    # page.locator('text=Innere (Inn) >> input[name="departments"]').check()
    # page.locator("text=Speichern").click()
    # page.locator("text=_pwt2_is_editor (Planen)").click()
    # page.locator('text=Innere (Inn) >> input[name="departments"]').check()
    # page.locator("text=Speichern").click()
    # page.locator("text=_pwt2_None (Lesen)").click()
    # page.locator('text=Innere (Inn) >> input[name="departments"]').check()
    # page.locator("text=Speichern").click()
    # page.locator("text=Mitarbeiter/innen").click()
    # page.locator("text=Person A").click()
    # page.locator("text=Funktionen").click()
    # page.locator("text=Ward A").click()
    # page.locator("text=Stationen").click()
    # page.locator("text=Dienste").click()
    # page.locator("text=Heute").click()
    # page.locator('a[role="button"]').click()
    # page.locator("text=Abmelden").click()
    # page.locator('[placeholder="Benutzername"]').click()
    # page.locator('[placeholder="Benutzername"]').fill("\t_pwt2_None")
    # page.locator('[placeholder="Benutzername"]').press("Alt+ArrowLeft")
    # page.locator('[placeholder="Benutzername"]').fill("_pwt2_None")
    # page.locator('[placeholder="Benutzername"]').press("Tab")
    # page.locator('[placeholder="Passwort"]').fill("123456")
    # page.locator('[placeholder="Passwort"]').press("Enter")
    # page.locator('a[role="button"]').click()
    # page.locator("text=Abmelden").click()
    # page.locator('[placeholder="Benutzername"]').click()
    # page.locator('[placeholder="Benutzername"]').fill("_pwt2_is_editor")
    # page.locator('[placeholder="Benutzername"]').press("Tab")
    # page.locator('[placeholder="Passwort"]').fill("123456")
    # page.locator('[placeholder="Passwort"]').press("Enter")
    # page.locator(".lacking").first.click()
    # page.locator(
    #     'div[role="dialog"]:has-text("× Besetzung ändern Freitag, 1.7.2022, Ward A Person A Person B «Juli 2022»MoDiMi")'
    # ).click()
    # page.locator(
    #     'div[role="dialog"]:has-text("× Besetzung ändern Freitag, 1.7.2022, Ward A Person A Person B «August 2022»MoDi")'
    # ).click()
    # page.locator("#changestaff >> text=×").click()
    # page.locator('a[role="button"]').click()
    # page.locator("text=Abmelden").click()
    context.close()
    browser.close()


def test_pw():
    with sync_playwright() as playwright:
        run(playwright)
