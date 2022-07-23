from time import sleep
from playwright.sync_api import Playwright, sync_playwright, expect

SERVER = "http://localhost:8000/"
PREFIX = "_pwt_"
COMPANY = "_pw_test_company"
COMPANY_SHORT = "_pw_test_c"
MAIL_ADDR = "_pwt_user@stationsplan.de"


def run_suite(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # Signup
    page.goto(SERVER + "delete_playwright_tests")
    page.goto(SERVER)
    page.locator("text=Ausblenden »").click()
    page.locator('a[role="button"]:has-text("Ausprobieren")').click()
    page.wait_for_url(SERVER + "offer")
    page.locator("text=Planung beginnen").click()
    page.wait_for_url(SERVER + "signup")
    page.locator('input[name="name"]').fill(COMPANY)
    page.locator('input[name="shortname"]').fill(COMPANY_SHORT)
    page.locator('select[name="region"]').select_option("15")
    page.locator('input[name="department"]').fill("Innere")
    page.locator('input[name="first_name"]').fill(PREFIX + "Vorname")
    page.locator('input[name="last_name"]').fill(PREFIX + "Nachname")
    page.locator('input[name="username"]').fill(PREFIX + "user")
    page.locator('input[name="email"]').fill(MAIL_ADDR)
    page.locator('input[name="password1"]').fill(PREFIX)
    page.locator('input[name="password2"]').fill(PREFIX)
    page.locator('button[type="submit"]:has-text("Anmelden")').click()
    page.wait_for_url(SERVER + "signup/success")
    expect(page.locator("#mail_sent_to")).to_have_text(MAIL_ADDR)

    page.goto(SERVER)
    # Login
    page.locator('[placeholder="Benutzername"]').fill("_pwt_user")
    page.locator('[placeholder="Passwort"]').fill("_pwt_")
    page.locator('[placeholder="Passwort"]').press("Enter")
    page.wait_for_url(SERVER + "setup/")

    # Make new department
    page.locator("text=Neue Abteilung").click()
    page.locator('input[name="name"]').fill("Chirurgie")
    page.locator('input[name="shortname"]').fill("Chi")
    page.locator("text=Speichern").click()

    # Make new employee
    page.locator("text=Neue/r Bearbeiter/in").click()
    page.locator('input[name="username"]').fill(PREFIX + "employee")
    page.locator('input[name="password1"]').fill("secret")
    page.locator('input[name="password2"]').fill("secret")
    page.locator('input[name="first_name"]').fill("Michael")
    page.locator('input[name="last_name"]').fill("Mustermann")
    page.locator('select[name="lvl"]').select_option("is_dep_lead")
    page.locator("#id_departments_0").check()
    page.locator("text=Speichern").click()

    # make new Person
    page.locator("text=Neue/r Mitarbeiter/in").click()
    expect(page.locator('div[role="dialog"]')).to_contain_text(
        "Mitarbeiter Name: Kurzname: Dienstantritt: Dienstende: Innere Chirurgie".split()
    )
    page.locator('input[name="name"]').fill("Koch")
    page.locator('input[name="shortname"]').fill("Koc")
    page.locator("#id_departments_0").check()
    page.locator('text=Oberärzte >> input[name="position"]').check()
    page.locator("text=Speichern").click()
    expect(page.locator("#person_list")).to_contain_text(
        ["Mitarbeiter/innen", "Koch"]
    )

    # Another Person
    page.locator("text=Neue/r Mitarbeiter/in").click()
    page.locator('input[name="name"]').fill("Meyer")
    page.locator('input[name="shortname"]').fill("Mey")
    page.locator("text=Speichern").click()
    expect(page.locator(".bg-danger")).to_contain_text(
        ["Abteilungen:", "Dieses Feld ist zwingend erforderlich."]
    )
    page.locator("#id_departments_0").check()
    page.locator("text=Speichern").click()
    expect(page.locator("#person_list")).to_contain_text(["Koch", "Meyer"])

    # make new ward
    page.locator("text=Neue Funktion").click()
    page.locator('input[name="name"]').fill("Station A")
    page.locator('input[name="shortname"]').fill("A")
    page.locator('input[name="min"]').fill("2")
    page.locator('input[name="max"]').fill("5")
    page.locator("#id_departments_1").check()
    page.locator("text=Speichern").click()
    expect(page.locator("#ward_list")).to_contain_text(
        ["Funktionen", "Station A"]
    )

    # Another ward
    page.locator("text=Neue Funktion").click()
    page.locator('input[name="name"]').fill("Station B")
    page.locator('input[name="shortname"]').fill("B")
    page.locator('input[name="min"]').fill("2")
    page.locator('input[name="max"]').fill("5")
    page.locator("text=Speichern").click()
    expect(page.locator(".bg-danger")).to_contain_text(
        ["Abteilungen", "Dieses Feld ist zwingend erforderlich."]
    )
    page.locator("#id_departments_1").check()
    expect(page.locator("#id_after_this")).to_contain_text(("Station A"))
    expect(page.locator("#id_not_with_this")).to_contain_text(("Station A"))
    page.locator("text=Speichern").click()
    expect(page.locator("#ward_list")).to_contain_text(
        ["Station A", "Station B"]
    )

    # Zuordnung
    page.locator("text=Personen und Funktionen zuordnen").click()
    page.wait_for_url(SERVER + "zuordnung/")
    checkboxes = page.locator('td input[type="checkbox"]')
    checkboxes.first.check()
    checkboxes.nth(1).check()
    checkboxes.nth(2).check()
    checkboxes.nth(3).check()

    sleep(1.0)
    page.close()
    context.close()
    browser.close()


def test_playwright():
    with sync_playwright() as playwright:
        run_suite(playwright)
