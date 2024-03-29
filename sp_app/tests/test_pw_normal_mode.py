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


@pytest.fixture
def changes_data(page):
    yield None
    page.goto(SERVER + "_delete_test_data")


def anmelden(page, username):
    page.goto(SERVER)
    page.locator("#username").fill(username)
    page.locator("#password").fill("123456")
    page.locator("#password").press("Enter")


def abmelden(page):
    page.locator(".glyphicon-cog").click()
    page.locator("text=Abmelden").click()


def check_content(locator, items, not_visible_items=[]):
    for i in items:
        expect(locator).to_contain_text(i)
    for i in not_visible_items:
        expect(locator).not_to_contain_text(i)


def check_tools_content(page, items, not_visible_items=[]):
    page.locator(".glyphicon-cog").click()
    check_content(page.locator(".dropdown-menu"), items, not_visible_items)
    page.locator(".glyphicon-cog").click()


def check_setup_nav_content(page, items, not_visible_items=[], active=None):
    check_content(page.locator("#setup-nav"), items, not_visible_items)
    if active is not None:
        expect(page.locator("#setup-nav li.active")).to_contain_text(active)


def add_department(page):
    NAME = "Test-Department"
    NAME2 = "Testing-Department"
    page.goto(SERVER + "setup/")
    check_content(
        page.locator("#dept-list"), ["Innere", "Chirurgie"], [NAME, NAME2]
    )
    # New department
    page.locator("text=Neue Abteilung").click()
    sleep(WAIT)
    page.locator("#id_name").fill(NAME)
    page.locator("#id_shortname").fill("Test-D")
    page.locator("text=Speichern").click()
    check_content(page.locator("#dept-list"), ["Innere", "Chirurgie", NAME])
    # Edit the name
    page.locator(f"text={NAME}").click()
    page.locator("#id_name").fill(NAME2)
    page.locator("text=Speichern").click()
    check_content(
        page.locator("#dept-list"), ["Innere", "Chirurgie", NAME2], [NAME]
    )


def add_employee(page, items, not_visible_items=[], is_admin=True):
    page.locator("text=Bearbeiter/innen").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items,
        not_visible_items + ["Test Employee"],
    )
    # New employee
    page.locator("text=Neue/r Bearbeiter/in").click()
    sleep(WAIT)
    page.locator("#id_username").fill("_Test-Employee")
    page.locator("#id_password1").fill("pa55w0rd")
    page.locator("#id_password2").fill("pa55w0rd")
    page.locator("#id_first_name").fill("Test")
    page.locator("#id_last_name").fill("Employee")
    expect(page.locator('select[name="lvl"] option')).to_have_count(
        4 if is_admin else 3
    )
    page.locator('select[name="lvl"]').select_option("is_editor")
    page.locator('text=Innere (Inn) >> input[name="departments"]').check()
    assert (
        is_admin
        == page.locator(
            'text=Chirurgie (Chi) >> input[name="departments"]'
        ).is_visible()
    )
    page.locator("text=Speichern").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items + ["Test Employee (Planen)"],
        not_visible_items,
    )
    # Change Name
    page.locator("text=Test Employee (Planen)").click()
    sleep(WAIT)
    page.locator("#id_first_name").fill("Testo")
    page.locator("text=Speichern").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items + ["Testo Employee (Planen)"],
        not_visible_items,
    )


def add_person(page, items, not_visible_items=[], chirurgie_visible=True):
    NAME1 = "Test-Person"
    NAME2 = "Testing-Person"
    page.locator("text=Mitarbeiter/innen").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items,
        not_visible_items + [NAME1, NAME2],
    )
    # New person
    page.locator("text=Neue/r Mitarbeiter/in").click()
    sleep(WAIT)
    page.locator("#id_name").fill(NAME1)
    page.locator("#id_shortname").fill("TP")
    page.locator("#id_position_4").click()  # Externe
    page.locator('text=Innere (Inn) >> input[name="departments"]').check()
    assert (
        chirurgie_visible
        == page.locator(
            'text=Chirurgie (Chi) >> input[name="departments"]'
        ).is_visible()
    )
    page.locator("text=Speichern").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items + [NAME1],
        not_visible_items + [NAME2],
    )
    # Change Name
    page.locator(f"text={NAME1}").click()
    sleep(WAIT)
    page.locator("#id_name").fill(NAME2)
    page.locator("text=Speichern").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items + [NAME2],
        not_visible_items + [NAME1],
    )


def add_ward(page, items, not_visible_items=[], chirurgie_visible=True):
    NAME1 = "Test-Ward"
    NAME2 = "Testing-Ward"
    page.locator("text=Funktionen").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items,
        not_visible_items + [NAME1, NAME2],
    )
    # New ward
    page.locator("text=Neue Funktion").click()
    sleep(WAIT)
    page.locator("#id_name").fill(NAME1)
    page.locator("#id_shortname").fill("TW")
    page.locator("#id_min").fill("2")
    page.locator("#id_max").fill("5")
    page.locator("#id_position").fill("2")
    page.locator('text=Innere (Inn) >> input[name="departments"]').check()
    assert (
        chirurgie_visible
        == page.locator(
            'text=Chirurgie (Chi) >> input[name="departments"]'
        ).is_visible()
    )
    page.locator("text=Speichern").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items + [NAME1],
        not_visible_items + [NAME2],
    )
    # Change Name
    page.locator(f"text={NAME1}").click()
    sleep(WAIT)
    page.locator("#id_name").fill(NAME2)
    page.locator("text=Speichern").click()
    sleep(WAIT)
    check_content(
        page.locator("#setup-tab"),
        items + [NAME2],
        not_visible_items + [NAME1],
    )


def zuordnen(page):
    page.locator("text=Zuordnung").click()
    sleep(WAIT)
    zuordnung = page.locator("tr:last-child td:last-child")
    expect(zuordnung).to_contain_text("❌")
    zuordnung.click()
    sleep(WAIT)
    expect(zuordnung).to_contain_text("✅")


def dienst_planen(page):
    page.goto(SERVER + "plan/20221001")
    # first_day_ward_a = page.locator(".wardrow:nth-child(2) td:nth-child(3)")
    first_lacking = page.locator(".lacking").first
    for person in ("A", "B"):
        expect(first_lacking).not_to_contain_text(person)
    first_lacking.click()
    page.locator('button:has-text("Person A")').click()
    # page.locator("text=Person A").click()
    page.locator("text=bis 03.10.2022 = 1 Tag").click()
    sleep(WAIT)
    expect(first_lacking).to_contain_text("A")


def test_as_company_admin(page, changes_data):
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
    add_department(page)
    add_employee(
        page,
        [
            "_pwt2_is_company_admin (Admin)",
            "_pwt2_is_dep_lead (Abteilungsleiter/in)",
            "_pwt2_is_editor (Planen)",
            "_pwt2_None (Lesen)",
        ],
    )
    add_person(page, ["Person A", "Person B", "Chirurg"], [])
    add_ward(page, ["Ward A", "Ward B"])
    zuordnen(page)
    dienst_planen(page)
    abmelden(page)


def test_as_dep_lead(page, changes_data):
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
    add_employee(
        page,
        [
            "_pwt2_is_dep_lead (Abteilungsleiter/in)",
            "_pwt2_is_editor (Planen)",
            "_pwt2_None (Lesen)",
        ],
        ["_pwt2_is_company_admin (Admin)"],
        is_admin=False,
    )
    add_person(
        page, ["Person A", "Person B"], ["Chirurg"], chirurgie_visible=False
    )
    add_ward(page, ["Ward A", "Ward B"], chirurgie_visible=False)
    zuordnen(page)
    dienst_planen(page)
    abmelden(page)


def test_as_editor(page, changes_data):
    anmelden(page, "_pwt2_is_editor")
    check_tools_content(
        page, ["Abmelden", "Passwort ändern"], ["Einstellungen", "Admin-Seite"]
    )
    dienst_planen(page)
    abmelden(page)


def test_as_None(page):
    anmelden(page, "_pwt2_None")
    check_tools_content(
        page, ["Abmelden"], ["Passwort ändern", "Einstellungen", "Admin-Seite"]
    )
    abmelden(page)
