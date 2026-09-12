"""Bounded, opt-in Bedrock evidence probe. Offline by default; fictional inputs only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import UTC, datetime

from hestiarelay.bedrock import BedrockPlanner
from hestiarelay.models import HouseholdGoal, HouseholdState, Preference


class ObservedClient:
    def __init__(self, client):
        self.client = client
        self.calls = 0
        self.response = {}
        self.request_sha256 = None

    def converse(self, **kwargs):
        if self.calls:
            raise ValueError("Probe permits one Converse request only.")
        canonical_request = json.dumps(kwargs, sort_keys=True, separators=(",", ":"))
        self.request_sha256 = hashlib.sha256(canonical_request.encode()).hexdigest()
        self.calls += 1
        self.response = self.client.converse(**kwargs)
        return self.response


def run_probe(*, live=False, approved=False, model_id=None, region="us-east-1", client=None):
    """`client` injection is for tests; mocked success is labeled separately."""
    state = HouseholdState(
        goal=HouseholdGoal(
            title="Fictional dinner", when="Friday evening", people=6, budget_usd=120
        ),
        preferences=[Preference(person="Ana", note="Fictional guest: allergic to nuts")],
        checklist=["Verify ingredients and guest constraints", "Review the $120 budget"],
    )
    report = {
        "schema_version": 2,
        "status": "READY_FOR_ACCOUNT_GATE",
        "mode": "offline",
        "converse_calls": 0,
        "live_aws_validated": False,
        "external_household_actions": 0,
        "credits_verified": False,
        "cost_usd": None,
        "evidence_complete": False,
        "phase2_complete": False,
    }
    if not live:
        # Do not resolve credentials, construct an AWS client or use ambient model configuration.
        planner = BedrockPlanner()
        planner.model_id = None
        plan = planner.generate_plan(state)
        return report | {"planner_source": plan.source, "fallback_reason": plan.fallback_reason}
    if not approved or not model_id or not region:
        raise ValueError("Live probe requires account/model/region and one-call approval.")
    planner = BedrockPlanner(model_id=model_id, region_name=region)
    injected = client is not None
    # Client creation may itself fail during credential discovery; redact that boundary too.
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        observed = ObservedClient(client if injected else planner._client_or_create())
    except (BotoCoreError, ClientError):
        return report | {"status": "BLOCKED", "mode": "live", "reason": "aws_client_unavailable"}
    planner._client = observed
    invoked_at = datetime.now(UTC).isoformat()
    started = time.monotonic()
    plan = planner.generate_plan(state)
    elapsed_ms = round((time.monotonic() - started) * 1000, 2)
    response = observed.response if isinstance(observed.response, dict) else {}
    usage = response.get("usage", {})
    usage = usage if isinstance(usage, dict) else {}
    counts = {
        key: value
        for key in ["inputTokens", "outputTokens", "totalTokens"]
        if type(value := usage.get(key)) is int and value >= 0
    }
    invocation_succeeded = plan.source == "amazon-bedrock" and plan.used_aws and observed.calls == 1
    usage_complete = len(counts) == 3
    usage_consistent = usage_complete and (
        counts["inputTokens"] + counts["outputTokens"] == counts["totalTokens"]
    )
    output_within_limit = usage_complete and counts["outputTokens"] <= 600
    # This text-only probe requires a completed answer. Truncation, tool requests,
    # filtering, unknown or missing stop reasons need review, never another call.
    stop_reason = response.get("stopReason")
    completion_confirmed = stop_reason == "end_turn"
    errors = []
    if not usage_complete:
        errors.append("usage_missing_or_invalid")
    elif not usage_consistent:
        errors.append("usage_total_mismatch")
    if usage_complete and not output_within_limit:
        errors.append("output_limit_exceeded")
    if not completion_confirmed:
        errors.append("completion_not_confirmed")
    success = invocation_succeeded and not errors
    status = "BLOCKED"
    if invocation_succeeded:
        status = (
            ("MOCK_PASS" if injected else "LIVE_CALL_PASS") if success else "EVIDENCE_INCOMPLETE"
        )
    return report | {
        "status": status,
        "mode": "injected-test" if injected else "live",
        "converse_calls": observed.calls,
        "live_aws_validated": success and not injected,
        "planner_source": plan.source,
        "fallback_reason": plan.fallback_reason,
        "elapsed_ms": elapsed_ms,
        "invoked_at_utc": invoked_at,
        "usage": counts,
        "usage_complete": usage_complete,
        "usage_consistent": usage_consistent,
        "completion_confirmed": completion_confirmed,
        "evidence_complete": success,
        "evidence_errors": errors,
        "request_sha256": observed.request_sha256,
        "model_id_sha256": hashlib.sha256(model_id.encode()).hexdigest(),
        "response_text_sha256": hashlib.sha256(plan.text.encode()).hexdigest(),
        "region": region,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Make at most one paid Converse call")
    parser.add_argument(
        "--approve-one-call",
        action="store_true",
        help="Use only after account, model pricing and spend gate are approved",
    )
    args = parser.parse_args(argv)
    try:
        report = run_probe(
            live=args.live,
            approved=args.approve_one_call,
            model_id=os.getenv("HESTIA_BEDROCK_MODEL_ID"),
            region=os.getenv("AWS_REGION", "us-east-1"),
        )
    except ValueError:
        report = {
            "status": "BLOCKED",
            "reason": "account_model_and_approval_required",
            "live_aws_validated": False,
            "converse_calls": 0,
        }
    print(json.dumps(report, indent=2))
    return 0 if report["status"] in {"READY_FOR_ACCOUNT_GATE", "MOCK_PASS", "LIVE_CALL_PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
