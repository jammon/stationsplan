from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    # Login
    page.goto("http://localhost:8000/")
    page.locator('[placeholder="Benutzername"]').fill("_pwt_user")
    page.locator('[placeholder="Passwort"]').fill("_pwt_")
    page.locator('[placeholder="Passwort"]').press("Enter")
    page.wait_for_url("http://localhost:8000/setup/")

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
    page.close()
    context.close()
    browser.close()


def test_persons_wards():
    with sync_playwright() as playwright:
        run(playwright)
