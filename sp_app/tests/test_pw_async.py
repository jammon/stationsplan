from time import sleep
import pytest
import asyncio
from playwright.async_api import Playwright, async_playwright, expect

SERVER = "http://localhost:8000/"
PREFIX = "_pwt_"
COMPANY = "_pw_test_company"
COMPANY_SHORT = "_pw_test_c"
MAIL_ADDR = "_pwt_user@stationsplan.de"


async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(SERVER + "delete_playwright_tests")
    await page.goto(SERVER)
    await page.locator('a[role="button"]:has-text("Ausprobieren")').click()
    await page.wait_for_url(SERVER + "offer")
    await page.locator("text=Planung beginnen").click()
    await page.wait_for_url(SERVER + "signup")
    await page.locator('input[name="name"]').fill(COMPANY)
    await page.locator('input[name="shortname"]').fill(COMPANY_SHORT)
    await page.locator('select[name="region"]').select_option("15")
    await page.locator('input[name="department"]').fill("Innere")
    await page.locator('input[name="first_name"]').fill(PREFIX + "Vorname")
    await page.locator('input[name="last_name"]').fill(PREFIX + "Nachname")
    await page.locator('input[name="username"]').fill(PREFIX + "user")
    await page.locator('input[name="email"]').fill(MAIL_ADDR)
    await page.locator('input[name="password1"]').fill(PREFIX)
    await page.locator('input[name="password2"]').fill(PREFIX)
    await page.locator('button[type="submit"]:has-text("Anmelden")').click()
    await page.wait_for_url(SERVER + "signup/success")
    await expect(page.locator("#mail_sent_to")).to_have_text(MAIL_ADDR)

    await page.goto(SERVER)
    # Login
    await page.locator('[placeholder="Benutzername"]').fill("_pwt_user")
    await page.locator('[placeholder="Passwort"]').fill("_pwt_")
    await page.locator('[placeholder="Passwort"]').press("Enter")
    await page.wait_for_url(SERVER + "setup/")

    # Make new department
    await page.locator("text=Neue Abteilung").click()
    await page.locator('input[name="name"]').fill("Chirurgie")
    await page.locator('input[name="shortname"]').fill("Chi")
    await page.locator("text=Speichern").click()

    # Make new employee
    sleep(0.1)
    await page.locator("#setup-employees").click(delay=100)
    sleep(0.1)
    await page.locator("text=Neue/r Bearbeiter/in").click(delay=100)
    await page.locator('input[name="username"]').fill(PREFIX + "employee")
    await page.locator('input[name="password1"]').fill("secret")
    await page.locator('input[name="password2"]').fill("secret")
    await page.locator('input[name="first_name"]').fill("Michael")
    await page.locator('input[name="last_name"]').fill("Mustermann")
    await page.locator('select[name="lvl"]').select_option("is_dep_lead")
    await page.locator("#id_departments_0").check()
    await page.locator("text=Speichern").click()

    # make new Person
    sleep(0.2)
    await page.locator("#setup-persons").click(delay=100)
    sleep(0.1)
    await page.locator("text=Neue/r Mitarbeiter/in").click()
    dialog = page.locator("#form-table")
    await expect(dialog).to_contain_text(
        [
            "Name:",
            "Kurzname:",
            "Dienstantritt:",
            "Dienstende:",
            "Innere",
            "Chirurgie",
        ]
    )
    await page.locator('input[name="name"]').fill("Koch")
    await page.locator('input[name="shortname"]').fill("Koc")
    await page.locator("#id_departments_0").check()
    await page.locator('text=Oberärzte >> input[name="position"]').check()
    await page.locator("text=Speichern").click()
    sleep(0.2)
    await expect(page.locator("#person_list")).to_contain_text(
        ["Mitarbeiter/innen", "Koch"]
    )

    # Another Person
    await page.locator("text=Neue/r Mitarbeiter/in").click()
    await page.locator('input[name="name"]').fill("Meyer")
    await page.locator('input[name="shortname"]').fill("Mey")
    await page.locator("text=Speichern").click()
    await expect(page.locator(".bg-danger")).to_contain_text(
        ["Abteilungen:", "Dieses Feld ist zwingend erforderlich."]
    )
    await page.locator("#id_departments_0").check()
    await page.locator("text=Speichern").click()
    sleep(0.2)
    await expect(page.locator("#person_list")).to_contain_text(
        ["Koch", "Meyer"]
    )

    # make new ward
    await page.locator("#setup-wards").click()
    sleep(0.1)
    await page.locator("text=Neue Funktion").click()
    await page.locator('input[name="name"]').fill("Station A")
    await page.locator('input[name="shortname"]').fill("A")
    await page.locator('input[name="min"]').fill("2")
    await page.locator('input[name="max"]').fill("5")
    await page.locator("#id_departments_1").check()
    await page.locator("text=Speichern").click()
    sleep(0.2)
    await expect(page.locator("#ward_list")).to_contain_text(
        ["Funktionen", "Station A"]
    )

    # Another ward
    await page.locator("text=Neue Funktion").click()
    await page.locator('input[name="name"]').fill("Station B")
    await page.locator('input[name="shortname"]').fill("B")
    await page.locator('input[name="min"]').fill("2")
    await page.locator('input[name="max"]').fill("5")
    await page.locator("text=Speichern").click()
    sleep(0.2)
    await expect(page.locator(".bg-danger")).to_contain_text(
        ["Abteilungen", "Dieses Feld ist zwingend erforderlich."]
    )
    await page.locator("#id_departments_1").check()
    await expect(page.locator("#id_after_this")).to_contain_text(("Station A"))
    await expect(page.locator("#id_not_with_this")).to_contain_text(
        ("Station A")
    )
    await page.locator("text=Speichern").click()
    sleep(0.2)
    await expect(page.locator("#ward_list")).to_contain_text(
        ["Station A", "Station B"]
    )

    # Zuordnung
    await page.locator("#setup-zuordnung").click()
    sleep(0.1)
    checkmarks = page.locator(".functions_view td")
    for i in range(4):
        await expect(checkmarks.nth(i)).to_contain_text("❌")

    await checkmarks.first.click()
    sleep(0.1)
    await expect(checkmarks.first).to_contain_text("✅")

    await context.close()
    await browser.close()


@pytest.mark.asyncio
async def xtest_async() -> None:
    async with async_playwright() as playwright:
        await run(playwright)
