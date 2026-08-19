import subprocess
import sys
import time
import urllib.request

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.fixture(scope="module")
def live_server():
    process = subprocess.Popen(  # noqa: S603
        [sys.executable, "run.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(60):
            try:
                with urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.2)
        else:
            raise AssertionError("Flask application did not start")
        reset = urllib.request.Request(
            "http://127.0.0.1:5000/api/lab/normal",
            method="POST",
        )
        with urllib.request.urlopen(reset, timeout=10) as response:
            assert response.status == 200
        yield "http://127.0.0.1:5000"
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_real_browser_acceptance_flows(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        page.goto(f"{live_server}/dashboard")
        expect(
            page.get_by_role("heading", name="Vehicle Identity Assurance Console")
        ).to_be_visible()
        page.goto(f"{live_server}/vehicles")
        expect(page.get_by_text("VT-7A82F1").first).to_be_visible()
        page.goto(f"{live_server}/vehicles/VT-7A82F1")
        expect(page.locator('[data-testid="oman-plate"]')).to_be_visible()

        page.goto(f"{live_server}/verify?vehicle=VT-7A82F1")
        page.select_option('select[name="responding_vehicle_id"]', "VT-7A82F1")
        page.get_by_role("button", name="Verify Vehicle").click()
        expect(page.get_by_role("heading", name="IDENTITY VERIFIED")).to_be_visible()
        expect(page.get_by_text("VERIFIED", exact=True)).to_be_visible()

        page.goto(f"{live_server}/security-lab")
        page.locator('form:has(input[value="swap"]) button').click()
        expect(page.locator(".lab-result dd").nth(2)).to_have_text("GENUINE PLATE WRONG VEHICLE")

        page.goto(f"{live_server}/security-lab")
        page.locator('form:has(input[value="replay"]) button').click()
        expect(page.locator(".lab-result dd").nth(2)).to_have_text("REPLAY DETECTED")

        page.goto(f"{live_server}/security-lab")
        page.locator('form:has(input[value="rebinding"]) button').click()
        expect(page.locator(".lab-result dd").nth(2)).to_have_text("VERIFIED")
        expect(page.get_by_text("PASS", exact=True)).to_be_visible()
        browser.close()


def test_responsive_no_horizontal_overflow(live_server):
    sizes = [(1440, 900), (1280, 720), (390, 844)]
    routes = [
        "/",
        "/dashboard",
        "/vehicles",
        "/vehicles/VT-7A82F1",
        "/verify",
        "/security-lab",
        "/lifecycle",
        "/audit",
        "/architecture",
    ]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width, height in sizes:
            page = browser.new_page(viewport={"width": width, "height": height})
            console_errors = []
            page.on(
                "console",
                lambda message, errors=console_errors: errors.append(message.text)
                if message.type == "error"
                else None,
            )
            for route in routes:
                page.goto(f"{live_server}{route}")
                overflow = page.evaluate(
                    "document.documentElement.scrollWidth > document.documentElement.clientWidth"
                )
                assert not overflow, f"Horizontal overflow at {width}x{height} on {route}"
                expect(page.get_by_text("Research Prototype", exact=False).first).to_be_visible()
            page.goto(f"{live_server}/vehicles/VT-7A82F1")
            expect(page.locator(".plate-oman")).to_have_attribute("dir", "rtl")
            expect(page.locator(".plate-qr")).to_be_visible()
            assert not console_errors, (
                f"Browser console errors at {width}x{height}: {console_errors}"
            )
            page.close()
        browser.close()
