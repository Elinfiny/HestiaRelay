#!/usr/bin/env bash
set -euo pipefail

test "${HESTIA_EXECUTION_APPROVED:-NO}" = "YES"
test "$(git rev-parse HEAD)" = "${HESTIA_SOURCE_COMMIT}"
git diff --quiet HEAD -- src requirements-proof.txt
export PYTHONPATH=src
python3 -c 'import sys; assert sys.version_info[:2] == (3, 12), "Reviewed Python 3.12 required"'
python3 -m venv /tmp/hestiarelay-proof-env
if ! /tmp/hestiarelay-proof-env/bin/pip install --quiet -r requirements-proof.txt > /tmp/hestiarelay-install.log 2>&1; then
  tail -c 8000 /tmp/hestiarelay-install.log
  exit 2
fi
/tmp/hestiarelay-proof-env/bin/ruff check .
if ! /tmp/hestiarelay-proof-env/bin/pytest --cov=hestiarelay --cov-report=term-missing > /tmp/hestiarelay-tests.log 2>&1; then
  tail -c 8000 /tmp/hestiarelay-tests.log
  exit 2
fi
tail -c 8000 /tmp/hestiarelay-tests.log
/tmp/hestiarelay-proof-env/bin/python -m hestiarelay.cloud_probe
