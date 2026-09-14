"""One ordinary signed-out playback check of the published submission video.

Runs only on a fresh GitHub-hosted browser, never on an owner's browser profile.
No sign-in, retries, response substitution, proxy changes or bot-check bypass.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://www.youtube.com/watch?v=NC2oy4x9Xdw"
TITLE = "HestiaRelay | A household plan that survives the next conversation"
OUTPUT = Path("qa-public-video")
MEDIA = """() => {
    const v = document.querySelector('video');
    return v ? {
        current_time: v.currentTime,
        duration: Number.isFinite(v.duration) ? v.duration : null,
        ready_state: v.readyState, paused: v.paused, ended: v.ended,
        error_code: v.error ? v.error.code : null,
        played: Array.from({length: v.played.length}, (_, i) =>
            [v.played.start(i), v.played.end(i)])
    } : null;
}"""
BLOCK = re.compile(
    r"confirm you(?:'|’)?re not a bot|verify you are human|unusual traffic|"
    r"this video is private|video unavailable|sign in to confirm your age",
    re.IGNORECASE,
)


def check(page, report):
    """Inspect rendered state, and stop on an explicit site/access gate."""
    text = page.locator("body").inner_text(timeout=10_000)
    blocked = BLOCK.search(text)
    if blocked:
        report["site_gate_text"] = blocked.group(0)
        raise RuntimeError("SITE_GATE: no automated recovery or sign-in attempted")
    sample = page.evaluate(MEDIA)
    report["media_samples"].append(sample)
    return sample


def main():
    OUTPUT.mkdir(exist_ok=True)
    report = {
        "schema": 1,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "expected_url": URL,
        "expected_title": TITLE,
        "status": "INCOMPLETE",
        "fresh_context": True,
        "credentials_or_storage_state_supplied": False,
        "reloads": 0,
        "seek_operations": 0,
        "play_clicks": 0,
        "media_samples": [],
        "limits": "One hosted Chromium observation; not a physical-device certification",
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        report["initial_cookie_count"] = len(context.cookies())
        page = context.new_page()
        page.set_default_timeout(10_000)
        try:
            response = page.goto(URL, wait_until="domcontentloaded", timeout=30_000)
            report["http_status"] = response.status if response else None
            # Cookie consent is a non-binding privacy choice, not authentication.
            reject = page.get_by_role("button", name="Reject all", exact=True)
            if reject.count() and reject.first.is_visible():
                reject.first.click()
            check(page, report)
            page.get_by_role("heading", name=TITLE, exact=True).wait_for()
            report["observed_url"] = page.url
            if page.url != URL:
                raise RuntimeError("Unexpected watch URL")
            report["signed_out_ui"] = page.get_by_role(
                "link", name="Sign in", exact=True
            ).count() > 0
            if report["initial_cookie_count"] != 0 or not report["signed_out_ui"]:
                raise RuntimeError("Signed-out precondition not demonstrated")
            page.locator("video").wait_for(state="attached")
            sample = check(page, report)
            if sample and sample["paused"]:
                play = page.get_by_role("button", name=re.compile(r"^Play(?: \(k\))?$"))
                for button in play.all():
                    if button.is_visible():
                        button.click()
                        report["play_clicks"] += 1
                        break
            deadline = time.monotonic() + 115
            captured = set()
            while time.monotonic() < deadline:
                sample = check(page, report)
                if sample:
                    if sample["error_code"]:
                        raise RuntimeError("Media element reported a playback error")
                    for moment in (20, 45, 78):
                        if sample["current_time"] >= moment and moment not in captured:
                            page.locator("video").screenshot(
                                path=str(OUTPUT / f"frame-{moment}.png")
                            )
                            captured.add(moment)
                    if sample["ended"]:
                        duration = sample["duration"]
                        covered = sample["played"]
                        if not 86.84 <= duration <= 88.84:
                            raise RuntimeError("Hosted duration differs from approved source")
                        if not any(a <= 1 and b >= duration - 0.5 for a, b in covered):
                            raise RuntimeError("Complete continuous playback not demonstrated")
                        report["status"] = "PASS"
                        report["full_playback_without_seeking"] = True
                        break
                page.wait_for_timeout(3_000)
            if report["status"] != "PASS":
                raise RuntimeError("Playback did not complete within the bounded observation")
        except Exception as error:
            # A site gate may appear during an earlier locator wait.
            with suppress(Exception):
                check(page, report)
            report["status"] = "BLOCKED" if "site_gate_text" in report else "FAIL"
            # Do not preserve exception stacks, request headers or signed media URLs.
            report["error_type"] = type(error).__name__
            report["reason"] = re.sub(r"https?://\S+", "[URL omitted]", str(error))[:600]
        finally:
            try:
                page.screenshot(path=str(OUTPUT / "final-page.png"), full_page=False)
            except Exception as error:
                report["screenshot_error_type"] = type(error).__name__
            report["finished_at_utc"] = datetime.now(UTC).isoformat()
            context.close()
            browser.close()
    (OUTPUT / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUTPUT.iterdir()}
    (OUTPUT / "sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
