"""Read the installed Inspector identity; never report an obsolete literal version."""

import ast
import hashlib
import json
from pathlib import Path

import pytest


def identity_function():
    module = ast.parse(Path("scripts/container_qa.py").read_text())
    function = next(
        n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == "inspector_identity"
    )
    namespace = {"Path": Path, "hashlib": hashlib, "json": json}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<identity>", "exec"), namespace)
    return namespace["inspector_identity"]


def test_installed_package_and_entry_are_bound(tmp_path):
    entry = tmp_path / "package/clients/launcher/build/index.js"
    entry.parent.mkdir(parents=True)
    entry.write_text("// synthetic package entry")
    package = tmp_path / "package/package.json"
    package.write_text(json.dumps({"name": "@modelcontextprotocol/inspector", "version": "9.8.7"}))
    result = identity_function()(entry)
    assert result["version"] == "9.8.7"
    assert result["entry_sha256"] == hashlib.sha256(entry.read_bytes()).hexdigest()
    assert result["package_sha256"] == hashlib.sha256(package.read_bytes()).hexdigest()


def test_unrelated_package_cannot_supply_identity(tmp_path):
    entry = tmp_path / "package/index.js"
    entry.parent.mkdir()
    entry.write_text("// synthetic unrelated package")
    (entry.parent / "package.json").write_text(json.dumps({"name": "unrelated", "version": "1"}))
    with pytest.raises(AssertionError):
        identity_function()(entry)
