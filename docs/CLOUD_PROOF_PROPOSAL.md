# One managed AWS proof — execution proposal

Prepared and explicitly approved 2026-09-12. **CONSUMED: one build and one
Converse call succeeded; all three temporary resources were removed after
verified evidence export.** See [the result](evidence/bedrock-20260912.json).
The proposal below is retained as the historical authorization boundary; it
must not be reused to launch another build. This was a temporary verification
job, not the judge-facing deployment or an Alexa+ integration.

## Exact scope

- Region: `us-east-1`; model: `amazon.nova-micro-v1:0`, on-demand Converse.
- Proposed stack: `hestiarelay-bedrock-proof-20260912`. Stop if that name already
  belongs to an existing resource; never adopt or replace unrelated resources.
- Template: `infra/bedrock-proof.json`. Exactly three new resources: a CodeBuild
  project, its dedicated IAM role, and a CloudWatch log group retained for one day.
- Source: public `Elinfiny/HestiaRelay`, detached at the reviewed immutable commit.
  Issue #4 records the exact merged SHA and CI run before approval is requested.
- Request: `infra/bedrock-proof-request.json`, fictional six-person Friday dinner,
  $120 budget and Ana's nut allergy. Canonical JSON SHA-256:
  `273965096cce1522a543a10ac250c848ba5ecf829469a2f98d12c5209ad0f960`.
- One build, one application Converse attempt, `maxTokens=600`, temperature 0.2,
  no SDK retry. A failed, incomplete or ambiguous invocation needs investigation
  and fresh authorization before any further billable attempt.

## Execution boundaries

The template never starts a build. Its approval variable defaults to `NO`.
After approval, create this stack with `CAPABILITY_IAM`, inspect the resulting
project and role, then submit exactly one `StartBuild` with a recorded unique
idempotency token and `HESTIA_EXECUTION_APPROVED=YES`. Record its returned build
ID before polling. An uncertain StartBuild result must be reconciled by reads;
never mint a new token and blindly repeat it.

CloudFormation creation and the IAM grant are part of the requested approval.
Application execution uses the dedicated service role; root credentials are
never passed to the build. Its trust is restricted to this account and exact
CodeBuild project. It can invoke only the selected foundation-model ARN and
write only its own log streams. It has no StartBuild, IAM, S3, purchase or
household-account permissions.

The managed Ubuntu image is pinned to `aws/codebuild/standard:7.0-26.07.29`
(observed in ListCuratedEnvironmentImages), with Python 3.12 selected explicitly.
`requirements-proof.txt` pins the validated Python dependency versions. Before
inference, the job checks the source commit, tracked source cleanliness, caller
role, managed project binding and exact request hash; lint and all Python tests
must pass. An exclusive attempt marker prevents a second call within that build.
This marker is not a cross-build quota: the executor must enforce one StartBuild.

No webhook, schedule, privileged Docker, VPC/NAT, S3 bucket, CodeConnection,
GitHub token, permanent AWS access key or customer-managed KMS key is introduced.
CloudWatch's default encryption is sufficient for this fixed fictional probe;
avoiding a new KMS key avoids an unnecessary recurring resource. Logs remain
private until reviewed. The probe deliberately includes the fictional response
for safety review; the normal CLI report remains redacted.

## Read-only account and price checks

AWS Core successfully returned STS identity, model metadata/availability,
Billing GetCredits and AWS Price List results on 2026-09-12. Nova Micro was
ACTIVE, AUTHORIZED and AVAILABLE in this region. Existing enabled credits cover
Bedrock; these are Free Tier/activity credits, **not evidence that the requested
hackathon award was granted**. Account identifiers, credit IDs and balances stay
out of the public repository. Recheck applicable credit coverage before starting.

Price List publication 2026-09-11, effective 2026-08-01:

| Item | Public SKU | USD rate |
| --- | --- | ---: |
| Nova Micro on-demand input | XAR69MSGZSU6FEM9 | 0.000035 / 1,000 tokens |
| Nova Micro on-demand output | YUSGHKDUPQRC75RK | 0.000140 / 1,000 tokens |
| Linux x86 CodeBuild general1.small, OnDemand-EC2 | 4Z79XP69AGHXE3C7 | 0.005 / minute |

Using an **estimate** of 1,000 input tokens, the 600-token output ceiling and
10 compute minutes: `0.000035 + 0.000084 + 0.050 = 0.050119 USD`, before small
log charges and any taxes. Input tokens have not been measured with CountTokens;
actual usage and build duration must be reconciled after the single run.

**Requested operational budget: USD 0.10 before credits.** The build timeout is
10 minutes, concurrency one, queued timeout five minutes, automatic retries zero.
The budget is an execution constraint, not an AWS-enforced dollar cutoff or a
guarantee of zero charges. If pricing, request, resources or expected costs change,
stop and revise the proposal before starting. No broader spending is authorized.

## Evidence, cleanup and acceptance

1. Check stack CREATE_COMPLETE, exact permissions and project configuration.
2. Start once; poll that build, collect `HESTIA_PROOF_REPORT` from its own logs.
3. Require source/request binding, dedicated-role verification, one real call,
   complete consistent usage, `end_turn` and live Bedrock provenance. Preserve
   latency and response digest; review text for budget/context retention, unsafe
   allergy assurances and invented actions. Failure cannot be relabeled success.
4. Calculate model cost from actual tokens and the above rates, record build
   minutes and log cost estimate. Credit application and final billing can lag.
5. Export and verify reviewed, redacted evidence in GitHub through a PR. Do not
   publish raw account/role/request IDs or unreviewed logs.
6. Delete only this newly created stack after evidence export, then explicitly
   delete its retained log group once preservation is verified. Include this
   cleanup in the execution approval; verify no project, role or log group remains.
7. Run regression CI and review Issue #4's remaining gates before closing it.
   A successful probe alone does not prove live Alexa+, AgentCore, Strands,
   production deployment, user impact or hackathon eligibility.

Validation before execution: cfn-lint 1.56.3, AWS ValidateTemplate (read-only),
policy regression assertions, pinned-environment CI, application tests and the
existing desktop/mobile browser CI. Resource creation/runtime success remains
unproven until the authorized run.

References:
[Converse](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Converse.html),
[CodeBuild pricing](https://aws.amazon.com/codebuild/pricing/),
[Bedrock pricing](https://aws.amazon.com/bedrock/pricing/),
[CountTokens](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_CountTokens.html).
