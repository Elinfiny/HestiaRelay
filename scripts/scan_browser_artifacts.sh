#!/usr/bin/env bash
# Scan decoded traces and demonstration sidecars before publishing review evidence.
set -euo pipefail
mkdir -p /tmp/hestia-browser-scan
curl --fail --silent --show-error --location --max-time 120 -o /tmp/hestia-browser-scan/gitleaks.tar.gz https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz
printf '%s\n' '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  /tmp/hestia-browser-scan/gitleaks.tar.gz' | sha256sum --check
tar -xzf /tmp/hestia-browser-scan/gitleaks.tar.gz -C /tmp/hestia-browser-scan gitleaks
/tmp/hestia-browser-scan/gitleaks dir qa-artifacts --redact=100 --max-decode-depth 2 --max-archive-depth 2 --report-format json --report-path qa-artifacts/demo/artifact-secrets.json
python - <<'PY'
import hashlib, json
from pathlib import Path
output = Path('qa-artifacts/demo')
files = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'sha256.json'}
(output / 'sha256.json').write_text(json.dumps(files, indent=2) + '\n')
PY
