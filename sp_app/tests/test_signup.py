import re
from playwright.sync_api import Playwright, sync_playwright, expect

SERVER = "http://localhost:8000/"
PREFIX = "_pwt_"
COMPANY = "_pw_test_company"
COMPANY_SHORT = "_pw_test_c"
MAIL_ADDR = "_pwt_user@stationsplan.de"


def run_signup(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
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
    page.close()
    context.close()
    browser.close()


def test_signup():
    with sync_playwright() as playwright:
        run_signup(playwright)
