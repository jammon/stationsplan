from playwright.sync_api import Playwright, sync_playwright, expect


def run_setup(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:8000/")
    # Login
    page.locator('[placeholder="Benutzername"]').fill("_pwt_user")
    page.locator('[placeholder="Passwort"]').fill("_pwt_")
    page.locator('[placeholder="Passwort"]').press("Enter")
    page.wait_for_url("http://localhost:8000/setup/")
    # Make new department
    page.locator("text=Neue Abteilung").click()
    page.locator('input[name="name"]').fill("Chirurgie")
    page.locator('input[name="shortname"]').fill("Chi")
    page.locator("text=Speichern").click()
    # Make new employee
    page.locator("text=Neue/r Bearbeiter/in").click()
    page.locator('input[name="username"]').fill("muster")
    page.locator('input[name="password1"]').fill("muster")
    page.locator('input[name="password2"]').fill("muster")
    page.locator('input[name="first_name"]').fill("Michael")
    page.locator('input[name="last_name"]').fill("Mustermann")
    page.locator('select[name="lvl"]').select_option("is_dep_lead")
    page.locator("#id_departments_0").check()
    page.locator("text=Speichern").click()
    page.close()
    context.close()
    browser.close()


def test_setup():
    with sync_playwright() as playwright:
        run_setup(playwright)
