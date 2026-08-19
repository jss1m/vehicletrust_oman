"""Capture evidence only after each real application flow reaches its asserted result."""

from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = "http://127.0.0.1:5000"
OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "hadatha" / "screenshots"


def capture(page, name: str) -> None:
    page.screenshot(path=OUTPUT / name, full_page=True)


def run_lab(page, scenario: str, expected: str, screenshot: str) -> None:
    page.goto(f"{BASE}/security-lab")
    page.locator(f'form:has(input[value="{scenario}"]) button').click()
    expect(page.locator(".lab-result dd").nth(2)).to_have_text(expected)
    expect(page.locator(".lab-result h2")).to_have_text("PASS")
    capture(page, screenshot)


def run_lifecycle(page, scenario: str, expected: str, screenshot: str) -> None:
    page.goto(f"{BASE}/lifecycle")
    page.locator(f'form:has(input[value="{scenario}"]) button').click()
    expect(page.locator(".overall")).to_contain_text("PASS")
    expect(page.locator(".overall")).to_contain_text(expected)
    capture(page, screenshot)


def run() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(120_000)
        page.set_default_navigation_timeout(120_000)

        page.request.post(f"{BASE}/api/lab/normal")
        page.goto(f"{BASE}/dashboard")
        expect(
            page.get_by_role("heading", name="Vehicle Identity Assurance Console")
        ).to_be_visible()
        capture(page, "01_dashboard.png")

        page.goto(f"{BASE}/registry")
        expect(page.get_by_text("VT-7A82F1").first).to_be_visible()
        capture(page, "02_vehicle_registry.png")

        page.goto(f"{BASE}/vehicles/VT-7A82F1")
        expect(page.locator('[data-testid="oman-plate"]')).to_be_visible()
        expect(page.locator('[data-testid="oman-plate"]').get_by_text("PLATE UID")).to_be_visible()
        capture(page, "03_compact_oman_prototype_plate.png")

        page.goto(f"{BASE}/credentials/issue")
        page.select_option('select[name="vehicle_id"]', "VT-C3D8E2")
        page.fill('input[name="plate_number"]', "68432")
        page.fill('input[name="plate_code"]', "CT")
        page.get_by_role("button", name="Issue Signed Credential").click()
        expect(page.get_by_role("heading", name="Credential Successfully Issued")).to_be_visible()
        capture(page, "04_credential_issued.png")

        page.goto(f"{BASE}/verify?vehicle=VT-7A82F1")
        page.select_option('select[name="responding_vehicle_id"]', "VT-7A82F1")
        page.get_by_role("button", name="Verify Vehicle").click()
        expect(page.get_by_role("heading", name="IDENTITY VERIFIED")).to_be_visible()
        capture(page, "05_vehicle_verified.png")

        run_lab(page, "swap", "GENUINE PLATE WRONG VEHICLE", "06_genuine_plate_wrong_vehicle.png")
        run_lab(page, "clone", "VEHICLE IDENTITY MISMATCH", "07_credential_clone_detected.png")
        run_lab(page, "tamper", "INVALID DIGITAL SIGNATURE", "08_tamper_detected.png")
        run_lab(page, "replay", "REPLAY DETECTED", "09_replay_detected.png")
        run_lab(page, "rebinding", "VERIFIED", "10_rebinding_verified.png")

        page.goto(f"{BASE}/security-lab")
        expect(page.get_by_role("heading", name="Security Lab")).to_be_visible()
        capture(page, "11_security_lab.png")

        page.get_by_role("button", name="Run Full Security Demo").click()
        expect(page.get_by_text("SECURITY DEMO PASSED", exact=True)).to_be_visible()
        capture(page, "12_full_security_demo.png")

        page.goto(f"{BASE}/audit")
        expect(page.get_by_role("heading", name="Security Audit Trail")).to_be_visible()
        capture(page, "13_audit_trail.png")

        page.goto(f"{BASE}/architecture")
        expect(
            page.get_by_role("heading", name="Independent Identity & Lifecycle Layers")
        ).to_be_visible()
        capture(page, "14_architecture.png")

        run_lab(page, "stolen", "VERIFIED IDENTITY STOLEN VEHICLE", "15_stolen_vehicle_alert.png")
        run_lifecycle(
            page,
            "multiple_vehicles",
            "INDEPENDENT ACTIVE BINDINGS",
            "16_owner_multiple_vehicles.png",
        )
        run_lifecycle(page, "sell_vehicle_keep_plate", "RESERVED PLATE", "17_plate_reserved.png")
        run_lifecycle(
            page,
            "sell_plate_number",
            "OLD PLATE RETIRED NEW PLATE ISSUED",
            "18_plate_number_sold.png",
        )
        capture(page, "19_old_plate_uid_retired.png")
        capture(page, "20_new_plate_uid_issued.png")
        run_lifecycle(page, "lost_plate", "OLD PLATE LOST NEW PLATE ISSUED", "21_lost_plate.png")

        page.goto(f"{BASE}/audit")
        expect(page.get_by_text("OLD PLATE LOST NEW PLATE ISSUED").first).to_be_visible()
        capture(page, "22_lifecycle_history.png")

        page.goto(f"{BASE}/security-lab")
        page.get_by_role("button", name="Run Full Security Demo").click()
        expect(page.get_by_text("Identity Lifecycle", exact=True)).to_be_visible()
        expect(page.get_by_text("SECURITY DEMO PASSED", exact=True)).to_be_visible()
        capture(page, "23_lifecycle_demo.png")
        browser.close()


if __name__ == "__main__":
    run()
