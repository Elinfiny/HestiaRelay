"""Execute the reviewed probe inside its isolated CodeBuild service role."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from hestiarelay.aws_probe import run_probe


def validate_gate(env: Mapping[str, str], actual_commit: str) -> None:
    """Fail before credential discovery or inference when approval/source binding is absent."""
    if env.get("HESTIA_EXECUTION_APPROVED") != "YES":
        raise ValueError("explicit_execution_approval_required")
    expected = env.get("HESTIA_SOURCE_COMMIT", "")
    if not re.fullmatch(r"[0-9a-f]{40}", expected) or expected != actual_commit:
        raise ValueError("source_commit_mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", env.get("HESTIA_REQUEST_SHA256", "")):
        raise ValueError("reviewed_request_hash_required")
    if not env.get("CODEBUILD_BUILD_ID", "").startswith(env.get("HESTIA_PROJECT_NAME", "") + ":"):
        raise ValueError("managed_build_binding_required")
    if not re.fullmatch(
        r"arn:aws:iam::[0-9]{12}:role/[A-Za-z0-9+=,.@_-]+", env.get("HESTIA_ROLE_ARN", "")
    ):
        raise ValueError("dedicated_role_required")


def verify_identity(role_arn: str, identity: dict) -> None:
    account = role_arn.split(":")[4]
    role_name = role_arn.rsplit("/", 1)[1]
    prefix = f"arn:aws:sts::{account}:assumed-role/{role_name}/"
    if identity.get("Account") != account or not identity.get("Arn", "").startswith(prefix):
        raise ValueError("dedicated_role_identity_mismatch")


def execute(env: Mapping[str, str] | None = None, marker: Path | None = None) -> dict:
    env = os.environ if env is None else env
    # The default cannot create an AWS client, even outside a Git checkout.
    if env.get("HESTIA_EXECUTION_APPROVED") != "YES":
        raise ValueError("explicit_execution_approval_required")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    validate_gate(env, commit)
    subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", "src", "requirements-proof.txt"], check=True
    )
    identity = boto3.client(
        "sts",
        region_name="us-east-1",
        config=Config(connect_timeout=3, read_timeout=12, retries={"max_attempts": 0}),
    ).get_caller_identity()
    verify_identity(env["HESTIA_ROLE_ARN"], identity)
    marker = Path("/tmp/hestiarelay-proof-attempt") if marker is None else marker
    # Re-running the command in this build must not spend again after an ambiguous result.
    with marker.open("x") as attempt:
        attempt.write(env["HESTIA_REQUEST_SHA256"])
    report = run_probe(
        live=True,
        approved=True,
        model_id="amazon.nova-micro-v1:0",
        region="us-east-1",
        expected_request_sha256=env["HESTIA_REQUEST_SHA256"],
        include_response=True,
    )
    return report | {
        "source_commit": commit,
        "dedicated_role_verified": True,
        "build_id_sha256": hashlib.sha256(env["CODEBUILD_BUILD_ID"].encode()).hexdigest(),
    }


def main() -> int:
    try:
        report = execute()
    except (ValueError, BotoCoreError, ClientError, OSError, subprocess.SubprocessError):
        # Errors can include role/account identifiers or request data. Preserve only a safe verdict.
        report = {"status": "BLOCKED", "live_aws_validated": False, "reason": "cloud_gate_failed"}
    print("HESTIA_PROOF_REPORT " + json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "LIVE_CALL_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
