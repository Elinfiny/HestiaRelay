"""Read the installed Inspector package instead of reporting an assumed version."""

import hashlib
import json
from pathlib import Path


def installed_inspector(executable):
    entry = Path(executable).resolve(strict=True)
    for parent in entry.parents:
        manifest = parent / "package.json"
        if not manifest.is_file():
            continue
        data = manifest.read_bytes()
        package = json.loads(data)
        if package.get("name") != "@modelcontextprotocol/inspector":
            continue
        expected_entry = (parent / package["bin"]["mcp-inspector"]).resolve(strict=True)
        if entry != expected_entry:
            raise ValueError("Executable is not the installed Inspector entry point")
        version = package.get("version")
        if version != "2.9.0":
            raise ValueError(f"Unexpected installed Inspector version: {version}")
        return {
            "version": version,
            "package_name": package["name"],
            "manifest_sha256": hashlib.sha256(data).hexdigest(),
            "entry_sha256": hashlib.sha256(entry.read_bytes()).hexdigest(),
        }
    raise ValueError("Installed Inspector package manifest not found")
