# Phase 2: one-call AWS evidence gate

The Phase 1 simulator works without AWS. This package prepares a controlled
live proof; it does not prove that the account, credits or model are available.

## Prepared, no credentials needed

```bash
python -m hestiarelay.aws_probe
```

Offline mode ignores ambient model configuration, creates no AWS client and
makes no AWS request. It returns machine-readable readiness evidence using
fictional canonical household data. Unit tests use injected clients and report
`MOCK_PASS`; they never count as live proof.

## Before a live call

The executor must verify the account and region through secure AWS access,
promotional-credit status, an enabled Converse-compatible model, current price
and an explicit one-call spending authorization. A request for credits is not
proof of awarded credits. No model/region choice is finalized before this gate.

Use temporary AWS credentials in the authorized cloud runtime. Do not paste
keys into chat, commit credentials, grant AdministratorAccess, create a paid
resource, subscribe to a model or accept marketplace terms as a side effect of
this preparation. Public GitHub Actions needs a separately reviewed OIDC role
and exact repository/ref or protected-environment trust; that role is not yet
created. No live workflow is enabled by this PR.

The required runtime action for Converse is `bedrock:InvokeModel`. Scope the
policy to the verified model or inference-profile resources; cross-region
profiles may require multiple concrete resource ARNs. Do not use a wildcard
example as if it were the final least-privilege policy.

## Controlled invocation, after the gate

Configure `HESTIA_BEDROCK_MODEL_ID` and `AWS_REGION` in the authorized cloud
runtime using the verified selection, then execute:

```bash
python -m hestiarelay.aws_probe --live --approve-one-call
```

At most one application-level Converse call, `maxTokens=600`, no SDK retry.
Credential-provider calls, if any, are separate from the reported Converse
count. Token limits and timeouts are not a dollar spending guarantee. The
probe records elapsed time and returned token usage; `cost_usd` remains unknown
until the actual price and billing/credit evidence are reconciled. The app uses
its existing Bedrock planner and deterministic failure boundary.

Preserve the stdout JSON with the exact source commit in the private operational
evidence location chosen for the AWS account, then publish only reviewed,
redacted evidence. This probe prints no credentials, account IDs, raw request
IDs, prompt or response text. Mocked success, fallback, missing usage or missing
account/credit evidence cannot close Phase 2. A failed/ambiguous invocation is
investigated before any new invocation; do not rerun unchanged automatically.

## Next executable steps

1. Securely authenticate the owner AWS account and inspect readiness read-only.
2. Select one suitable enabled model and calculate the one-call cost boundary.
3. Prepare the exact credential/permission route and obtain only required approval.
4. Make one authorized call, inspect its output and provenance, and preserve evidence.
5. Verify the canonical UI/MCP/consent regression gates. Evaluate AgentCore or
   Strands only when there is a measurable continuity/orchestration benefit.

References checked 2026-09-12:
[Converse API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html),
[model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html).
