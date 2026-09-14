#!/usr/bin/env bash
# CI-only release audit. No AWS commands, credentials, automatic fixes or blanket allowlists.
set -euo pipefail
out=qa-artifacts/release
mkdir -p "$out" /tmp/hestia-audit-bin
python -m venv /tmp/hestia-audit-tools
/tmp/hestia-audit-tools/bin/pip install pip-audit==2.10.1 bandit==1.8.6
curl --fail --silent --show-error --location --max-time 120 -o /tmp/hestia-trivy.tar.gz https://github.com/aquasecurity/trivy/releases/download/v0.74.0/trivy_0.74.0_Linux-64bit.tar.gz
printf '%s\n' '2ae6fe3ee734b7fdf11335663e18c75ea12dccc76062f09f164a3b0f8be4371a  /tmp/hestia-trivy.tar.gz' | sha256sum --check
curl --fail --silent --show-error --location --max-time 120 -o /tmp/hestia-gitleaks.tar.gz https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz
printf '%s\n' '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  /tmp/hestia-gitleaks.tar.gz' | sha256sum --check
tar -xzf /tmp/hestia-trivy.tar.gz -C /tmp/hestia-audit-bin trivy
tar -xzf /tmp/hestia-gitleaks.tar.gz -C /tmp/hestia-audit-bin gitleaks
export PATH="/tmp/hestia-audit-bin:$PATH"
# Preserve all completed reports even when a later gate fails. Exit codes are evidence.
set +e
gitleaks git . --log-opts=--all --redact=100 --report-format json --report-path "$out/history-secrets.json"
history_status=$?
gitleaks dir qa-artifacts --redact=100 --max-decode-depth 2 --max-archive-depth 2 --report-format json --report-path "$out/artifact-secrets.json"
artifact_status=$?
/tmp/hestia-audit-tools/bin/pip-audit --strict --disable-pip --no-deps -r requirements-proof.txt -f json -o "$out/python-advisories.json"
python_status=$?
# Include build/backend, browser and template-validation dependencies actually resolved in CI.
python -m pip freeze --all --exclude-editable > "$out/build-requirements.txt"
/tmp/hestia-audit-tools/bin/pip-audit --strict --disable-pip --no-deps -r "$out/build-requirements.txt" -f json -o "$out/build-advisories.json"
build_status=$?
/tmp/hestia-audit-tools/bin/bandit -q -r src -f json -o "$out/source-static-analysis.json"
source_status=$?
npm audit --prefix /tmp/hestiarelay-inspector --json > "$out/npm-advisories.json"
npm_status=$?
trivy image --scanners vuln --format json --output "$out/image-advisories.json" --exit-code 0 hestiarelay:judge
image_status=$?
trivy image --format cyclonedx --scanners license --license-full --output "$out/image-sbom.cdx.json" hestiarelay:judge
sbom_status=$?
trivy --version --format json > "$out/scanner-version.json"
set -e
export HESTIA_SCAN_STATUSES="$history_status $artifact_status $python_status $build_status $source_status $npm_status $image_status $sbom_status"
python scripts/release_inventory.py
