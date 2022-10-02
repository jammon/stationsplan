import pytest
import urllib
from django.conf import settings
from playwright.sync_api import Playwright, sync_playwright, expect
from time import sleep


SERVER = "http://localhost:8000/"
WAIT = 0.3

no_test_reason = ""
if not settings.SERVER_TYPE == "dev":
    pytest.skip("skipping dev-only tests", allow_module_level=True)
else:
    try:
        response = urllib.request.urlopen(SERVER)
        if response.status >= 400:
            no_test_reason = "Dev-Server returns error"
    except urllib.error.URLError:
        no_test_reason = "Dev-Server not ready"
if no_test_reason:
    pytest.skip(no_test_reason, allow_module_level=True)


def anmelden(page, username):
    page.goto(SERVER)
    page.locator("#username").fill(username)
    page.locator("#password").fill("123456")
    page.locator("#password").press("Enter")


def abmelden(page):
    page.locator(".glyphicon-cog").click()
    page.locator("text=Abmelden").click()


def check_content(locator, items, not_items):
    expect(locator).to_contain_text(items)
    # see https://github.com/microsoft/playwright/issues/16083
    for i in not_items:
        expect(locator).not_to_contain_text(i)


def check_tools_content(page, items, not_items=[]):
    page.locator(".glyphicon-cog").click()
    check_content(page.locator(".dropdown-menu"), items, not_items)
    page.locator(".glyphicon-cog").click()


def check_setup_nav_content(page, items, not_items=[], active=None):
    check_content(page.locator("#setup-nav"), items, not_items)
    if active is not None:
        expect(page.locator("#setup-nav li.active")).to_contain_text(active)


def edit_dept(page, dept):
    "Change name of department"
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


def check_setup_persons(page, items, not_items=[]):
    page.locator("text=Mitarbeiter/innen").click()
    sleep(WAIT)
    check_content(page.locator("#setup-tab"), items, not_items)


def check_setup_wards(page, items, not_items=[]):
    page.locator("text=Funktionen").click()
    sleep(WAIT)
    check_content(page.locator("#setup-tab"), items, not_items)


def test_as_company_admin(page):
    anmelden(page, "_pwt2_is_company_admin")
    check_tools_content(
        page, ["Abmelden", "Passwort ändern", "Einstellungen"], ["Admin-Seite"]
    )
    page.goto(SERVER + "setup/")
    check_setup_nav_content(
        page,
        [
            "Abteilungen",
            "Bearbeiter/innen",
            "Mitarbeiter/innen",
            "Funktionen",
            "Zuordnung",
        ],
        active="Abteilungen",
    )
    edit_dept(page, "Innere")
    edit_dept(page, "Chirurgie")
    check_setup_persons(page, ["Person A", "Person B", "Chirurg"], [])
    check_setup_wards(page, ["Ward A", "Ward B"])
    abmelden(page)


def test_as_dep_lead(page):
    anmelden(page, "_pwt2_is_dep_lead")
    check_tools_content(
        page, ["Abmelden", "Passwort ändern", "Einstellungen"], ["Admin-Seite"]
    )
    page.goto(SERVER + "setup/")
    check_setup_nav_content(
        page,
        ["Bearbeiter/innen", "Mitarbeiter/innen", "Funktionen", "Zuordnung"],
        ["Abteilungen"],
        active="Bearbeiter/innen",
    )
    check_setup_persons(page, ["Person A", "Person B"], ["Chirurg"])
    check_setup_wards(page, ["Ward A", "Ward B"])
    abmelden(page)


def test_as_editor(page):
    anmelden(page, "_pwt2_is_editor")
    check_tools_content(
        page, ["Abmelden", "Passwort ändern"], ["Einstellungen", "Admin-Seite"]
    )
    abmelden(page)


def test_as_None(page):
    anmelden(page, "_pwt2_None")
    check_tools_content(
        page, ["Abmelden"], ["Passwort ändern", "Einstellungen", "Admin-Seite"]
    )
    abmelden(page)

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


# def test_pw():
#     with sync_playwright() as playwright:
#         run(playwright)
