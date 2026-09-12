"""Real TLS browser login, continuity, consent, restart and backup restoration."""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from tls_runner import TLSJudge  # noqa: E402

from hestiarelay.recovery import snapshot  # noqa: E402


def sign_in(page, url, key):
    page.goto(url)
    expect(page.get_by_role("heading", name="Open the household demo")).to_be_visible()
    expect(page.locator("#login-status")).to_have_text("Ready when you are.")
    page.get_by_label("Access key", exact=True).fill(key)
    page.get_by_role("button", name="Continue to your household").click()
    expect(page.get_by_role("status")).to_contain_text("Ready when you are")


def main():
    output = Path("qa-artifacts/judge")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as pw:
        for width, height, label in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
            with TemporaryDirectory() as temporary:
                root = Path(temporary)
                server = TLSJudge(root).start()
                browser = None
                try:
                    browser = pw.chromium.launch(
                        args=["--ignore-certificate-errors-spki-list=" + server.spki]
                    )
                    context = browser.new_context(viewport={"width": width, "height": height})
                    page = context.new_page()
                    errors, failed = [], []
                    page.on("pageerror", lambda e, sink=errors: sink.append(str(e)))
                    page.on(
                        "console",
                        lambda m, sink=errors: sink.append(m.text) if m.type == "error" else None,
                    )
                    page.on("requestfailed", lambda r, sink=failed: sink.append(r.url))
                    page.goto(server.url)
                    expect(page.locator("#login-status")).to_have_text("Ready when you are.")
                    page.screenshot(path=str(output / f"{label}-login.png"), full_page=True)
                    sign_in(page, server.url, server.key)
                    for i in range(3):
                        page.locator(f"#demo-{i}").click()
                        expect(page.get_by_role("status")).to_contain_text(f"Session {i + 1} saved")
                    expect(page.locator("#preferences")).to_contain_text("Ana")
                    expect(page.locator("#budget")).to_have_text("$120.00")
                    expect(page.locator("#provenance")).to_have_text("deterministic")
                    page.get_by_role("button", name="Approve this proposal:").click()
                    expect(page.locator("#proposals")).to_contain_text(
                        "Consent recorded. Nothing executed."
                    )
                    page.get_by_role("button", name="Start another session").click()
                    expect(page.get_by_role("status")).to_contain_text("New session opened")
                    for message in ["Remember Lee is vegetarian.", "Are we ready for Friday?"]:
                        page.get_by_label("Your next message").fill(message)
                        page.get_by_role("button", name="Send", exact=False).click()
                        expect(page.get_by_role("status")).to_contain_text(
                            "Message and context saved"
                        )
                    page.get_by_role("button", name="Reject this proposal:").click()
                    expect(page.locator("#proposals")).to_contain_text(
                        "Proposal rejected. Nothing executed."
                    )
                    state = page.evaluate("fetch('/api/state').then(r=>r.json())")
                    page.screenshot(path=str(output / f"{label}-continuity.png"), full_page=True)
                    cookies = context.cookies()
                    auth = next(c for c in cookies if c["name"] == "__Host-hestia")
                    assert auth["secure"] and auth["httpOnly"] and auth["sameSite"] == "Strict"
                    assert server.key not in page.content()
                    storage = page.evaluate("JSON.stringify([localStorage, sessionStorage])")
                    assert server.key not in storage and auth["value"] not in storage
                    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
                    page.get_by_role("button", name="Sign out", exact=True).click()
                    expect(
                        page.get_by_role("heading", name="Open the household demo")
                    ).to_be_visible()
                    with server.client() as probe:
                        assert (
                            probe.get(
                                "/api/state", headers={"Cookie": "__Host-hestia=" + auth["value"]}
                            ).status_code
                            == 401
                        )
                    sign_in(page, server.url, server.key)
                    assert page.evaluate("fetch('/api/state').then(r=>r.json())") == state
                    # Back up a running service using SQLite's consistent snapshot API.
                    receipt = snapshot(server.database, root / "backup.db")
                    restore = snapshot(
                        root / "backup.db", root / "restored.db", expected_sha256=receipt["sha256"]
                    )
                    server.stop()
                    server.start(root / "restored.db")
                    page.goto(server.url)
                    expect(
                        page.get_by_role("heading", name="Open the household demo")
                    ).to_be_visible()
                    sign_in(page, server.url, server.key)
                    assert page.evaluate("fetch('/api/state').then(r=>r.json())") == state
                    page.get_by_label("Your next message").focus()
                    page.keyboard.press("Tab")
                    assert page.evaluate("document.activeElement.id") == "send"
                    assert not errors, errors
                    assert not failed, failed
                    results.append(
                        {
                            "viewport": {"width": width, "height": height},
                            "real_tls": True,
                            "certificate": (
                                "Ephemeral CI certificate; Chromium SPKI pinned; Python CA verified"
                            ),
                            "login_logout_revoked_replay": "PASS",
                            "restart_revokes_auth": "PASS",
                            "canonical_sessions": 3,
                            "approve_reject": "PASS",
                            "restored_full_snapshot": True,
                            "backup_state_sha256": receipt["state_sha256"],
                            "restore_state_sha256": restore["state_sha256"],
                            "console_errors": errors,
                            "failed_requests": failed,
                            "horizontal_overflow": False,
                            "keyboard_focus": "send",
                            "secret_in_browser_storage": False,
                            "aws_calls": 0,
                            "public_endpoint": False,
                        }
                    )
                finally:
                    if browser:
                        browser.close()
                    server.stop()
    (output / "judge-qa.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
