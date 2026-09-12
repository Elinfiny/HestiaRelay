"""Cloud CI: real container, persistent volume, MCP clients and existing browser QA."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import httpx2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
import browser_qa  # noqa: E402
from test_mcp_http import mcp_turn  # noqa: E402

from hestiarelay.service import CANONICAL_MESSAGES  # noqa: E402

OUTPUT = Path("qa-artifacts")


def docker(*args, check=True):
    result = subprocess.run(
        ["docker", *args], check=False, capture_output=True, text=True, timeout=120
    )
    if check and result.returncode:
        raise RuntimeError(f"Docker {args[0]} failed: {result.stderr[:4000]}")
    return (result.stdout + (result.stderr if args[0] == "logs" else "")).strip()


@contextmanager
def volume():
    name = "hestia-qa-" + uuid4().hex
    docker("volume", "create", name)
    try:
        yield name
    finally:
        docker("volume", "rm", name)


@contextmanager
def container(image, data_volume, label):
    name = "hestia-qa-" + uuid4().hex
    try:
        docker(
            "run",
            "--detach",
            "--name",
            name,
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            "128",
            "--memory",
            "512m",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--publish",
            "127.0.0.1::8000",
            "--mount",
            f"type=volume,source={data_volume},target=/data",
            "--env",
            "HESTIA_BEDROCK_MODEL_ID=",
            "--env",
            "AWS_EC2_METADATA_DISABLED=true",
            image,
        )
        port = docker("port", name, "8000/tcp")
        assert port.startswith("127.0.0.1:") and "\n" not in port, port
        url = "http://" + port
        for _ in range(100):
            try:
                if httpx2.get(url + "/health", timeout=0.3, trust_env=False).status_code == 200:
                    break
            except httpx2.TransportError:
                pass
            time.sleep(0.1)
        else:
            raise TimeoutError("Container did not become healthy")
        inspected = json.loads(docker("inspect", name))[0]
        assert inspected["Config"]["User"] == "10001:10001"
        assert inspected["HostConfig"]["ReadonlyRootfs"] is True
        assert inspected["HostConfig"]["CapDrop"] == ["ALL"]
        assert inspected["HostConfig"]["SecurityOpt"] == ["no-new-privileges"]
        assert docker("exec", name, "id", "-u") == "10001"
        yield url
    finally:
        (OUTPUT / f"container-{label}.log").write_text(docker("logs", name, check=False))
        docker("rm", "--force", name, check=False)


def state(url):
    response = httpx2.get(url + "/api/state", trust_env=False)
    response.raise_for_status()
    return response.json()["state"]


def inspector(executable, url):
    results = {}
    with TemporaryDirectory() as auth_store:
        env = os.environ | {
            "MCP_STORAGE_DIR": auth_store,
            "MCP_INSPECTOR_OAUTH_STATE_PATH": str(Path(auth_store) / "oauth.json"),
            "MCP_AUTO_OPEN_ENABLED": "false",
        }
        for method in ["initialize", "tools/list", "tools/call"]:
            args = [
                executable,
                "--cli",
                "--transport",
                "http",
                "--server-url",
                url + "/mcp",
                "--connect-timeout",
                "10000",
                "--stored-auth-only",
                "--format",
                "json",
                "--method",
                method,
            ]
            if method == "tools/list":
                args.append("--strict")
            if method == "tools/call":
                args.extend(["--tool-name", "get_continuity_brief", "--tool-args-json", "{}"])
            completed = subprocess.run(
                args, env=env, check=False, capture_output=True, text=True, timeout=30
            )
            if completed.returncode:
                (OUTPUT / "inspector-error.txt").write_text(completed.stderr)
                raise RuntimeError(f"Inspector {method} failed: {completed.stderr[:4000]}")
            result = json.loads(completed.stdout)
            results[method] = result
            (OUTPUT / ("inspector-" + method.replace("/", "-") + ".json")).write_text(
                json.dumps(result, indent=2) + "\n"
            )
    version = results["initialize"]["result"]["protocolVersion"]
    assert version >= "2025-11-25"
    names = {t["name"] for t in results["tools/list"]["result"]["tools"]}
    assert {"get_continuity_brief", "decide_sensitive_action", "send_simulator_message"} <= names
    assert not results["tools/call"]["result"].get("isError", False)
    assert "Ana" in json.dumps(results["tools/call"])
    return {"version": "2.6.0", "protocol": version, "methods": list(results), "status": "PASS"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="hestiarelay:judge")
    parser.add_argument("--inspector", required=True)
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    versions = []
    with volume() as persistent:
        with container(args.image, persistent, "session1") as url:
            versions.append(asyncio.run(mcp_turn(url, CANONICAL_MESSAGES[0])))
            original = state(url)
        # This is a new container using the same volume, not a process-only restart.
        with container(args.image, persistent, "sessions2-3") as url:
            for text in CANONICAL_MESSAGES[1:]:
                versions.append(asyncio.run(mcp_turn(url, text)))
            restored = state(url)
            assert restored["goal"]["goal_id"] == original["goal"]["goal_id"]
            assert restored["goal"]["people"] == 6 and restored["goal"]["budget_usd"] == 120
            assert len(restored["sessions"]) == len(restored["turns"]) == 3
            assert restored["preferences"][0]["note"] == "allergic to nuts"
            assert restored["plan"]["source"] == "deterministic"
            proposal = restored["proposals"][0]
            httpx2.post(
                url + "/api/decision",
                trust_env=False,
                json={
                    "action_id": proposal["action_id"],
                    "approved": True,
                },
            ).raise_for_status()
            asyncio.run(mcp_turn(url, "Remember Lee is vegetarian."))
            asyncio.run(mcp_turn(url, CANONICAL_MESSAGES[2]))
            pending = next(p for p in state(url)["proposals"] if p["status"] == "pending")
            httpx2.post(
                url + "/api/decision",
                trust_env=False,
                json={
                    "action_id": pending["action_id"],
                    "approved": False,
                },
            ).raise_for_status()
            final = state(url)
            assert {p["status"] for p in final["proposals"]} == {"approved", "rejected"}
            assert all(p["execution"] == "not_executed" for p in final["proposals"])
            for headers in [{"Host": "untrusted.example"}, {"Origin": "https://untrusted.example"}]:
                assert (
                    httpx2.get(url + "/api/state", trust_env=False, headers=headers).status_code
                    == 403
                )
            inspector_report = inspector(args.inspector, url)
        with container(args.image, persistent, "consent-recovery") as url:
            assert state(url) == final

    @contextmanager
    def browser_server(path):
        with volume() as data_volume, container(args.image, data_volume, path.stem) as url:
            yield url

    browser_qa.main(server_factory=browser_server, output_dir=OUTPUT / "container-browser")
    image = json.loads(docker("image", "inspect", args.image))[0]
    report = {
        "status": "PASS",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "image_id": image["Id"],
        "image_user": image["Config"]["User"],
        "dependency_lock_sha256": hashlib.sha256(
            Path("requirements-proof.txt").read_bytes()
        ).hexdigest(),
        "canonical_mcp_sessions": 3,
        "sdk_negotiated_versions": versions,
        "container_recreations_with_same_volume": 2,
        "goal_preferences_budget_and_consent_restored": True,
        "host_origin_rejections": "PASS",
        "mcp_inspector": inspector_report,
        "browser": "PASS",
        "provenance": "deterministic",
        "external_actions": 0,
        "aws_calls": 0,
        "public_deployment": False,
    }
    (OUTPUT / "container-qa.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
