"""CI-owned Chromium QA against a real Python service, with reviewable screenshots."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_mcp_http import running_server  # noqa: E402


def main():
    output = Path("qa-artifacts")
    output.mkdir(exist_ok=True)
    reports = []
    with sync_playwright() as playwright, TemporaryDirectory() as temporary:
        browser = playwright.chromium.launch()
        for width, height, label in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
            with running_server(Path(temporary) / f"{label}.db") as url:
                context = browser.new_context(viewport={"width": width, "height": height})
                context.tracing.start(screenshots=True, snapshots=True)
                page = context.new_page()
                errors, failed_requests = [], []
                page.on("pageerror", lambda error, sink=errors: sink.append(str(error)))
                page.on(
                    "console",
                    lambda msg, sink=errors: sink.append(msg.text) if msg.type == "error" else None,
                )
                page.on(
                    "requestfailed", lambda request, sink=failed_requests: sink.append(request.url)
                )
                page.goto(url)
                expect(page.get_by_role("status")).to_contain_text("Ready when you are")
                page.screenshot(path=str(output / f"{label}-initial.png"), full_page=True)
                # Real clicks, real service, real SQLite; no response interception or fixtures.
                for index in range(3):
                    page.locator(f"#demo-{index}").click()
                    expect(page.get_by_role("status")).to_contain_text(f"Session {index + 1} saved")
                state = context.request.get(url + "/api/state").json()["state"]
                goal = state["goal"]["goal_id"]
                assert all(s["recovered_goal_id"] == goal for s in state["sessions"][1:])
                assert len(state["sessions"]) == 3 and len(state["turns"]) == 3
                expect(page.locator("#preferences")).to_contain_text("allergic to nuts")
                expect(page.locator("#provenance")).to_have_text("deterministic")
                expect(page.locator("#budget")).to_have_text("$120.00")
                expect(page.locator("#spent")).to_have_text("$0")
                page.screenshot(path=str(output / f"{label}-session3.png"), full_page=True)
                page.get_by_role("button", name="Approve this proposal:").click()
                expect(page.locator("#proposals")).to_contain_text(
                    "Consent recorded. Nothing executed."
                )
                page.reload()
                expect(page.locator("#proposals")).to_contain_text(
                    "Consent recorded. Nothing executed."
                )
                # A separate browser context has no sessionStorage; server data remains.
                fresh = browser.new_context(viewport={"width": width, "height": height})
                recovered = fresh.new_page()
                recovered.goto(url)
                expect(recovered.locator("#preferences")).to_contain_text("allergic to nuts")
                expect(recovered.locator("#goal-evidence")).to_contain_text(goal)
                recovered.close()
                fresh.close()
                # A new constraint invalidates old context; a new pending proposal can be rejected.
                page.get_by_role("button", name="Start another session").click()
                expect(page.get_by_role("status")).to_contain_text("New session opened")
                page.get_by_label("Your next message").fill("Remember Lee is vegetarian.")
                page.get_by_role("button", name="Send", exact=False).click()
                expect(page.get_by_role("status")).to_contain_text("Message and context saved")
                page.get_by_label("Your next message").fill("Are we ready for Friday?")
                page.get_by_role("button", name="Send", exact=False).click()
                expect(page.get_by_role("status")).to_contain_text("Message and context saved")
                page.get_by_role("button", name="Reject this proposal:").click()
                expect(page.locator("#proposals")).to_contain_text(
                    "Proposal rejected. Nothing executed."
                )
                page.get_by_label("Your next message").fill("")
                page.keyboard.press("Tab")
                focus = page.evaluate("document.activeElement.id")
                assert focus == "send"
                overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
                assert not overflow
                assert not errors, errors
                assert not failed_requests, failed_requests
                reports.append(
                    {
                        "viewport": {"width": width, "height": height},
                        "canonical_sessions": 3,
                        "goal_recovered": True,
                        "approve_reject": "PASS",
                        "reload": "PASS",
                        "fresh_browser_context": "PASS",
                        "horizontal_overflow": overflow,
                        "keyboard_focus": focus,
                        "console_errors": errors,
                        "failed_requests": failed_requests,
                        "provenance": "deterministic",
                        "external_actions": 0,
                    }
                )
                context.tracing.stop(path=str(output / f"{label}-trace.zip"))
                context.close()
        browser.close()
    (output / "browser-qa.json").write_text(json.dumps(reports, indent=2) + "\n")
    members = sorted(output.iterdir())
    with (output / "MANIFEST.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["relative_path", "size_bytes", "sha256"])
        for member in members:
            if member.is_file() and member.name != "MANIFEST.csv":
                data = member.read_bytes()
                writer.writerow([member.name, len(data), hashlib.sha256(data).hexdigest()])
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
