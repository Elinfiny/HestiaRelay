"""The version gate reads real installed bytes and refuses drift before network use."""

import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "inspector_version", Path(__file__).resolve().parents[1] / "scripts/inspector_version.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def installation(tmp_path, version="2.9.0", name="@modelcontextprotocol/inspector"):
    package = tmp_path / "node_modules/@modelcontextprotocol/inspector"
    entry = package / "clients/launcher/build/index.js"
    entry.parent.mkdir(parents=True)
    entry.write_text("// owned inert entry fixture\n")
    (package / "package.json").write_text(json.dumps({
        "name": name, "version": version,
        "bin": {"mcp-inspector": "clients/launcher/build/index.js"},
    }))
    link = tmp_path / "inspector"
    link.symlink_to(entry)
    return link, entry


def test_actual_installed_version_and_entry_hash(tmp_path):
    link, entry = installation(tmp_path)
    result = module.installed_inspector(link)
    assert result["version"] == "2.9.0"
    original = result["entry_sha256"]
    entry.write_text("// changed entry\n")
    assert module.installed_inspector(link)["entry_sha256"] != original


@pytest.mark.parametrize("version", ["2.6.0", "2.9.1", None])
def test_version_drift_refuses(tmp_path, version):
    link, _ = installation(tmp_path, version=version)
    with pytest.raises(ValueError, match="Unexpected installed"):
        module.installed_inspector(link)


def test_wrong_package_refuses(tmp_path):
    link, _ = installation(tmp_path, name="unrelated")
    with pytest.raises(ValueError, match="manifest not found"):
        module.installed_inspector(link)


def test_wrong_entry_refuses(tmp_path):
    _, entry = installation(tmp_path)
    other = entry.with_name("other.js")
    other.write_text("// inert\n")
    with pytest.raises(ValueError, match="entry point"):
        module.installed_inspector(other)


def test_missing_entry_refuses(tmp_path):
    with pytest.raises(FileNotFoundError):
        module.installed_inspector(tmp_path / "missing")
