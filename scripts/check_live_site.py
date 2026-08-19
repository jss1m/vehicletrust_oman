"""Validate an authorized public VehicleTrust demo URL without mutating it."""

import ipaddress
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ROUTES = [
    "/",
    "/healthz",
    "/readyz",
    "/registry",
    "/verify",
    "/security-lab",
    "/lifecycle",
    "/audit",
    "/architecture",
]
ASSETS = [
    "/static/bootstrap.min.css",
    "/static/styles.css",
    "/static/compact.css",
    "/static/app.js",
    "/static/img/vehicle_identity.svg",
    "/static/img/architecture_flow.svg",
]


def check(url: str) -> bool:
    base = url.rstrip("/")
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != "https":
        print("[FAIL] Public demo URL must use HTTPS")
        return False
    if not parsed.hostname or parsed.hostname.lower() == "localhost":
        print("[FAIL] Public demo URL must have a public hostname")
        return False
    try:
        address = ipaddress.ip_address(parsed.hostname)
        if not address.is_global:
            print("[FAIL] Public demo URL cannot use a private or loopback address")
            return False
    except ValueError:
        pass
    passed = True
    for path in ROUTES + ASSETS:
        target = f"{base}{path}"
        try:
            request = urllib.request.Request(
                target, headers={"User-Agent": "VehicleTrust-Live-Check/1"}
            )
            # The base URL is rejected above unless it is HTTPS and non-local.
            with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310
                ok = 200 <= response.status < 400
                content_type = response.headers.get("Content-Type", "")
                print(f"[{'PASS' if ok else 'FAIL'}] {path} {response.status} {content_type}")
                passed = passed and ok
        except (urllib.error.URLError, TimeoutError) as exc:
            print(f"[FAIL] {path} {exc}")
            passed = False
    return passed


def main() -> int:
    url = os.getenv("PUBLIC_DEMO_URL") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not url:
        print("PUBLIC_DEMO_URL is required. No live deployment was claimed or tested.")
        return 2
    return 0 if check(url) else 1


if __name__ == "__main__":
    raise SystemExit(main())
