"""Real SDK client, real TCP server, distinct transports, and a process restart."""

from __future__ import annotations

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from uuid import uuid4

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from hestiarelay.service import CANONICAL_MESSAGES


@contextmanager
def running_server(path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = os.environ | {"HESTIA_STATE_DB": str(path), "HESTIA_BEDROCK_MODEL_ID": ""}
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "hestiarelay.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                if httpx2.get(url + "/health", timeout=0.3, trust_env=False).status_code == 200:
                    break
            except httpx2.TransportError:
                if process.poll() is not None:
                    raise RuntimeError("MCP server exited before startup") from None
                time.sleep(0.1)
        else:
            raise TimeoutError("MCP server did not become ready")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


async def mcp_turn(url, text):
    async with (
        httpx2.AsyncClient(trust_env=False) as http_client,
        streamable_http_client(url + "/mcp", http_client=http_client) as streams,
        ClientSession(*streams) as client,
    ):
        initialized = await client.initialize()
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        assert {
            "start_household_goal",
            "remember_household_preference",
            "get_continuity_brief",
            "generate_household_plan",
            "propose_household_action",
            "decide_sensitive_action",
            "start_simulator_session",
            "send_simulator_message",
        } <= names
        session_id = str(uuid4())
        started = await client.call_tool("start_simulator_session", {"session_id": session_id})
        assert not started.is_error
        result = await client.call_tool(
            "send_simulator_message",
            {
                "session_id": session_id,
                "request_id": str(uuid4()),
                "text": text,
            },
        )
        assert not result.is_error
        return initialized.protocol_version


def test_real_mcp_three_sessions_across_process_restart(tmp_path):
    database = tmp_path / "mcp.db"
    versions = []
    with running_server(database) as url:
        versions.append(asyncio.run(mcp_turn(url, CANONICAL_MESSAGES[0])))
        first = httpx2.get(url + "/api/state", trust_env=False).json()["state"]
        # Also exercise an explicit initialization at the competition's minimum baseline.
        response = httpx2.post(
            url + "/mcp",
            trust_env=False,
            headers={
                "Accept": "application/json, text/event-stream",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "hestia-baseline-smoke", "version": "1.0"},
                },
            },
        )
        assert response.status_code == 200
        baseline = response.json()["result"]["protocolVersion"]
        assert baseline == "2025-11-25"
    with running_server(database) as url:
        versions.append(asyncio.run(mcp_turn(url, CANONICAL_MESSAGES[1])))
        versions.append(asyncio.run(mcp_turn(url, CANONICAL_MESSAGES[2])))
        state = httpx2.get(url + "/api/state", trust_env=False).json()["state"]
        assert state["goal"]["goal_id"] == first["goal"]["goal_id"]
        assert len(state["sessions"]) == 3
        assert state["preferences"][0]["note"] == "allergic to nuts"
        assert state["proposals"][0]["status"] == "pending"
        assert len(state["turns"]) == 3
        assert state["plan"]["source"] == "deterministic"
    assert all(version >= "2025-11-25" for version in versions)
    print(
        "MCP_EVIDENCE="
        + json.dumps(
            {
                "transport": "streamable-http",
                "sdk_negotiated_versions": versions,
                "explicit_baseline": baseline,
                "distinct_sessions": 3,
                "restart": "PASS",
                "external_actions": 0,
            }
        )
    )
