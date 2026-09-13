"""Record real UI interactions; caption only the surrounding video, never alter app data/DOM."""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_mcp_http import running_server  # noqa: E402


async def read_mcp(url):
    async with (
        httpx2.AsyncClient(trust_env=False) as http,
        streamable_http_client(url + "/mcp", http_client=http) as streams,
        ClientSession(*streams) as client,
    ):
        initialized = await client.initialize()
        tools = await client.list_tools()
        result = await client.call_tool("get_continuity_brief", {})
        assert not result.is_error
        return {
            "transport": "Streamable HTTP",
            "protocol": initialized.protocol_version,
            "tool_names": [t.name for t in tools.tools],
            "result": result.model_dump(mode="json"),
            "same_running_app": True,
        }


def stamp(seconds):
    milliseconds = round(seconds * 1000)
    return f"00:{milliseconds // 60000:02}:{milliseconds // 1000 % 60:02},{milliseconds % 1000:03}"


def main():
    output = Path("qa-artifacts/demo")
    output.mkdir(parents=True, exist_ok=True)
    captions, errors, failures = [], [], []
    with sync_playwright() as playwright, TemporaryDirectory() as temporary:
        database = Path(temporary) / "fictional-demo.db"
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            record_video_dir=str(output / "raw"),
            record_video_size={"width": 1440, "height": 1000},
        )
        page = context.new_page()
        started = time.monotonic()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda request: failures.append(request.url))

        def scene(name, text, selector=None, seconds=6):
            if selector:
                page.locator(selector).scroll_into_view_if_needed()
            captions.append({"start": time.monotonic() - started, "text": text, "scene": name})
            page.screenshot(path=str(output / f"{len(captions):02}-{name}.png"))
            page.wait_for_timeout(seconds * 1000)

        with running_server(database) as url:
            page.goto(url)
            expect(page.get_by_role("status")).to_contain_text("Ready when you are")
            scene(
                "opening",
                "HestiaRelay | Pick up where life left off.\n"
                "Real app. Fictional household. Alexa+ simulation; deterministic planner.",
            )
            page.locator("#demo-0").click()
            expect(page.get_by_role("status")).to_contain_text("Session 1 saved")
            scene(
                "session-one",
                "Session 1: Six people, Friday evening, $120.\n"
                "The service saves the goal, budget and preparation tasks.",
                "#conversation",
            )
            first = context.request.get(url + "/api/state").json()["state"]
            page.locator("#demo-1").click()
            expect(page.get_by_role("status")).to_contain_text("Session 2 saved")
            scene(
                "session-two",
                "Session 2: Remember Ana is allergic to nuts.\n"
                "Only this new message is sent. The existing household goal is recovered.",
                "#preferences",
            )
            page.locator("#demo-2").click()
            expect(page.get_by_role("status")).to_contain_text("Session 3 saved")
            scene(
                "session-three",
                "Session 3: Are we ready for Friday?\n"
                "Six guests, $120 and Ana's constraint remain in the same household.",
                "#conversation",
                8,
            )
            scene(
                "provenance",
                "The plan identifies its source: deterministic.\n"
                "Tasks are reminders. Planner advice cannot verify food safety.",
                "#provenance",
            )
            scene(
                "exact-proposal",
                "Sensitive actions stop at this exact proposal.\n"
                "Approval applies only to its saved details and current context.",
                "#proposals",
                8,
            )
            page.get_by_role("button", name="Approve this proposal:").click()
            expect(page.locator("#proposals")).to_contain_text(
                "Consent recorded. Nothing executed."
            )
            scene(
                "approved",
                "Consent recorded. Nothing executed.\n"
                "No purchase, payment, message or account change is performed.",
                "#proposals",
            )
            before_restart = context.request.get(url + "/api/state").json()["state"]
        # The process exits; a new process reads the same SQLite file.
        with running_server(database) as url:
            page.goto(url)
            expect(page.locator("#preferences")).to_contain_text("allergic to nuts")
            recovered = context.request.get(url + "/api/state").json()["state"]
            assert recovered == before_restart
            assert recovered["goal"]["goal_id"] == first["goal"]["goal_id"]
            assert len(recovered["sessions"]) == 3
            scene(
                "restart",
                "The server has restarted, with the same database.\n"
                "All three sessions and the exact consent decision survived.",
                "#timeline",
                8,
            )
            page.get_by_role("button", name="Start another session").click()
            expect(page.get_by_role("status")).to_contain_text("New session opened")
            for message in ["Remember Lee is vegetarian.", "Are we ready for Friday?"]:
                page.get_by_label("Your next message").fill(message)
                page.get_by_role("button", name="Send", exact=False).click()
                expect(page.get_by_role("status")).to_contain_text("Message and context saved")
            scene(
                "new-context",
                "A new constraint changes the proposal context.\n"
                "Earlier approval does not authorize this new proposal.",
                "#proposals",
            )
            page.get_by_role("button", name="Reject this proposal:").click()
            expect(page.locator("#proposals")).to_contain_text(
                "Proposal rejected. Nothing executed."
            )
            scene(
                "rejected",
                "This exact proposal is rejected. Nothing executed.\n"
                "Your decisions persist alongside the household plan.",
                "#proposals",
            )
            mcp = json.loads(
                subprocess.check_output(
                    [sys.executable, __file__, "--mcp", url],
                    text=True,
                )
            )
            assert "Ana" in json.dumps(mcp["result"])
            brief = "\n".join(item.get("text", "") for item in mcp["result"]["content"])
            evidence_page = output / "mcp-receipt.html"
            evidence_page.write_text(
                '<!doctype html><html lang="en"><meta charset="utf-8">'
                "<title>HestiaRelay — recorded MCP evidence</title><style>"
                "body{margin:80px;background:#f8f5ef;color:#172c24;font:24px system-ui;}"
                "h1{font-size:48px;}pre{white-space:pre-wrap;line-height:1.7;"
                "padding:36px;background:white;border-radius:16px;font:28px system-ui;}"
                "small{color:#526354;}</style><small>RECORDED EVIDENCE · REAL SDK CLIENT</small>"
                "<h1>One household. Two real interfaces.</h1><p>Streamable HTTP · Protocol "
                + html.escape(mcp["protocol"])
                + "</p><p>Tool: get_continuity_brief</p><pre>"
                + html.escape(brief)
                + "</pre><p>This output came from the same running "
                "service used in the browser. No additional model call.</p>"
                "<small>Evidence presentation · not the application interface</small></html>"
            )
            page.goto(evidence_page.resolve().as_uri())
            scene(
                "mcp",
                "A real MCP client just read this same household over Streamable HTTP.\n"
                "Protocol and tool output are preserved in mcp-evidence.json.",
                None,
                8,
            )
            page.goto(url)
            scene(
                "closing",
                "One household thread, across separate sessions. Your decisions stay yours.\n"
                "Public MIT source: github.com/Elinfiny/HestiaRelay | Draft for visual review.",
                "footer",
                8,
            )
            final_state = context.request.get(url + "/api/state").json()["state"]
        assert not errors, errors
        assert not failures, failures
        end = time.monotonic() - started
        video = page.video
        context.close()
        raw_path = video.path()
        browser.close()
    srt = []
    for index, entry in enumerate(captions):
        until = captions[index + 1]["start"] if index + 1 < len(captions) else end
        srt.append(f"{index + 1}\n{stamp(entry['start'])} --> {stamp(until)}\n{entry['text']}\n")
    (output / "captions.srt").write_text("\n".join(srt))
    # Caption band below the unmodified browser recording; silent, accessible text candidate.
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(raw_path),
            "-vf",
            "pad=1440:1120:0:0:color=0x172C24,subtitles=qa-artifacts/demo/captions.srt:"
            "force_style='FontName=DejaVu Sans,FontSize=14,PrimaryColour=&HFFFFFF,"
            "Outline=0,Alignment=2,MarginV=10'",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output / "hestiarelay-candidate.mp4"),
        ],
        check=True,
    )
    duration = float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(output / "hestiarelay-candidate.mp4"),
            ],
            text=True,
        )
    )
    assert duration < 180
    report = {
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "duration_seconds": duration,
        "status": "DRAFT_FOR_OWNER_VISUAL_REVIEW",
        "audio": "none; English captions",
        "canonical_sessions": 3,
        "process_restart_state_equal": True,
        "real_mcp_same_household": True,
        "provenance": "deterministic",
        "live_aws_calls": 0,
        "external_actions": 0,
        "live_alexa_connection": False,
        "console_errors": errors,
        "failed_requests": failures,
        "scenes": captions,
    }
    for name, data in [
        ("demo-report.json", report),
        ("mcp-evidence.json", mcp),
        ("fictional-state.json", final_state),
    ]:
        (output / name).write_text(json.dumps(data, indent=2) + "\n")
    files = {
        str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "sha256.json"
    }
    (output / "sha256.json").write_text(json.dumps(files, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--mcp":
        print(json.dumps(asyncio.run(read_mcp(sys.argv[2]))))
    else:
        main()
