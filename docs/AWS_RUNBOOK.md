# Phase 2: one-call AWS evidence gate

The Phase 1 simulator works without AWS. Account/model/credit metadata has now
been verified read-only; live inference is still unproven. The prepared route is
[one managed CodeBuild proof](CLOUD_PROOF_PROPOSAL.md), with a dedicated role and
an exact source/request binding. Its financial/resource approval is pending.

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
proof of awarded credits. The reviewed selection is Nova Micro in `us-east-1`;
recheck access before execution.

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

Evidence schema 2 requires all three nonnegative integer token counts, a total
equal to input plus output, output within the requested 600-token ceiling, and
`stopReason=end_turn`. Missing or contradictory usage, truncation, filtering,
or tool requests produce `EVIDENCE_INCOMPLETE` and exit code 2 even when the
service returned text. This result requires investigation; it never triggers
an automatic retry. `BLOCKED` remains the verdict for invocation/fallback failure.

The report includes UTC invocation time and SHA-256 of the exact canonical JSON
request passed to the SDK, without emitting its contents. `MOCK_PASS` always
has `live_aws_validated=false`. Even `LIVE_CALL_PASS` leaves `phase2_complete=false`:
account, credits, approved cost, source-commit binding and output review are
separate required evidence. The hash binds a request; it does not attest that
an account was authenticated or that the output is safe.

Preserve the stdout JSON with the exact source commit in the private operational
evidence location chosen for the AWS account, then publish only reviewed,
redacted evidence. The default CLI report prints no credentials, account IDs,
raw request IDs, prompt or response text. The managed runner opts in to the fixed
fictional response in private logs for review; redact it before publication.
Mocked success, fallback, missing usage or missing
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

## AWS Core connection check

Verify plugin installation, exposed operation tools and authenticated account
access separately. AWS Core skills being installed is not proof that AWS API
tools or credentials are available. Discover both connected tools and eligible
plugins before declaring an access blocker. Keep failures of the cloud execution
surface separate from AWS service availability. The observed session limitation
is tracked in F-003 and Issue #4; no owner PC is a project dependency.
