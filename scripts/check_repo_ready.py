"""Fail closed when required release evidence or repository hygiene is missing."""

import os
import re
import subprocess  # nosec B404
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "FINAL_BUILD_REPORT.md",
    "requirements.txt",
    "requirements-dev.txt",
    ".gitignore",
    ".env.example",
    "Procfile",
    "render.yaml",
    "wsgi.py",
    ".github/workflows/ci.yml",
    "tests",
    "docs",
    "docs/ARCHITECTURE.md",
    "docs/THREAT_MODEL.md",
    "docs/SECURITY_TEST_MATRIX.md",
    "docs/hadatha/HADATHA_ALIGNMENT.md",
    "docs/hadatha/HADATHA_FORM_CONTENT_AR.md",
    "docs/hadatha/SECURITY_TEST_MATRIX.md",
    "docs/hadatha/screenshots",
    "vehicletrust/static",
    "vehicletrust/templates",
    "scripts",
]
SCREENSHOTS = [
    "01_dashboard.png",
    "02_vehicle_registry.png",
    "03_compact_oman_prototype_plate.png",
    "04_credential_issued.png",
    "05_vehicle_verified.png",
    "06_genuine_plate_wrong_vehicle.png",
    "07_credential_clone_detected.png",
    "08_tamper_detected.png",
    "09_replay_detected.png",
    "10_rebinding_verified.png",
    "11_security_lab.png",
    "12_full_security_demo.png",
    "13_audit_trail.png",
    "14_architecture.png",
    "15_stolen_vehicle_alert.png",
    "16_owner_multiple_vehicles.png",
    "17_plate_reserved.png",
    "18_plate_number_sold.png",
    "19_old_plate_uid_retired.png",
    "20_new_plate_uid_issued.png",
    "21_lost_plate.png",
    "22_lifecycle_history.png",
    "23_lifecycle_demo.png",
]
IGNORED_DIRS = {
    ".git",
    ".venv",
    ".release_venv",
    "instance",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".yaml", ".yml", ".html", ".js", ".css", ".toml"}
SUSPICIOUS = [
    re.compile(r"-----BEGIN (?:EC |RSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api_key|password|secret_key|token)\s*=\s*['\"][^'\"\s]{12,}"),
]
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)")


def visible_files():
    for directory, names, filenames in os.walk(ROOT):
        names[:] = [name for name in names if name not in IGNORED_DIRS]
        base = Path(directory)
        for filename in filenames:
            yield base / filename


def tracked_files() -> set[str]:
    result = subprocess.run(  # nosec B603, B607
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.replace("\\", "/") for line in result.stdout.splitlines()}


def has_exact_case(path: Path) -> bool:
    """Verify GitHub/Linux-compatible path casing while running on Windows."""
    try:
        relative = path.relative_to(ROOT)
    except ValueError:
        return False
    current = ROOT
    for part in relative.parts:
        if part not in {child.name for child in current.iterdir()}:
            return False
        current /= part
    return current.is_file()


def markdown_image_failures() -> list[str]:
    failures: list[str] = []
    for markdown in (path for path in visible_files() if path.suffix.lower() == ".md"):
        content = markdown.read_text(encoding="utf-8", errors="ignore")
        for match in MARKDOWN_IMAGE.finditer(content):
            target = match.group("target").strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "data:")):
                continue
            candidate = (markdown.parent / target).resolve()
            if not has_exact_case(candidate):
                relative = markdown.relative_to(ROOT)
                failures.append(f"broken or case-mismatched image link in {relative}: {target}")
    return failures


def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            failures.append(f"missing required path: {relative}")
    if not any((ROOT / "tests").glob("test_*.py")):
        failures.append("no pytest test files found")
    screenshot_root = ROOT / "docs" / "hadatha" / "screenshots"
    for name in SCREENSHOTS:
        if not (screenshot_root / name).is_file():
            failures.append(f"missing screenshot: {name}")
    tracked = tracked_files()
    forbidden_tracked = [
        path for path in tracked if path.endswith((".env", ".db", ".sqlite", ".sqlite3", ".pem"))
    ]
    failures.extend(f"forbidden tracked file: {path}" for path in forbidden_tracked)
    for path in visible_files():
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {
            "Procfile",
            ".env.example",
        }:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SUSPICIOUS:
            if pattern.search(text):
                failures.append(f"possible secret material: {path.relative_to(ROOT)}")
    failures.extend(markdown_image_failures())
    if failures:
        print("REPOSITORY NOT READY")
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1
    print("[PASS] Required release structure")
    print("[PASS] No tracked .env, database or PEM private-key files")
    print("[PASS] No obvious secret values in repository text")
    print(f"[PASS] {len(SCREENSHOTS)} required Hadatha screenshots")
    print("[PASS] Local Markdown image links and path casing")
    print("REPOSITORY READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
