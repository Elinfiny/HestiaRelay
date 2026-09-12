from __future__ import annotations

import importlib


def test_mcp_server_builds_with_streamable_http_app(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HESTIA_STATE_DB", str(tmp_path / "server.db"))
    module = importlib.import_module("hestiarelay.server")

    assert module.app is not None
    assert module.mcp is not None
    assert module.planner.configured is False
