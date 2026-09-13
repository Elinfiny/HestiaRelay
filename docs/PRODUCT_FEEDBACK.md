# Product feedback — evidence-based preparation

These are project assessment notes for the submission rehearsal, not a claim
that feedback has been sent. Conclusions cover this repository and its recorded
runs. No owner experience, service outage or benchmark is invented. The
[friction log](FRICTION_LOG.md) preserves reproduction steps and limitations.

## MCP Python SDK and Streamable HTTP

**Use:** The real server exposes bounded continuity, planning and exact-consent
tools. The browser and MCP share one household service. **Worked well:** SDK
clients and Inspector 2.6.0 negotiate protocol 2025-11-25 and recover the same
persisted household across connections and container restarts. **Onboarding:**
The bootstrap established a working server; later phases added actual TCP,
Inspector and process-restart evidence. **Needs work:** Remote household identity
and authorization are still project work. Local interoperability does not make
an Internet-exposed MCP endpoint safe. **Use again:** Yes, for a bounded tool
surface whose authorization and effects remain in the application. Evidence:
[container guide](CONTAINER_GUIDE.md), [release receipt](evidence/release-20260913.json).

## Amazon Bedrock Runtime, Nova Micro and boto3

**Use:** The Python adapter actually invokes `converse` and labels planner
provenance; an explicit deterministic path handles unavailable configuration or
provider failures. **Worked well:** One approved Nova Micro invocation returned
a reviewed fictional plan, 222 input tokens, 230 output tokens and 1,114.44 ms
observed call duration. **Onboarding:** Offline and mocked tests preceded the
account/model/permission checks and one controlled live proof. Initial AWS Core
operation discovery was unavailable in one session and later worked; F-003 is
tooling friction, not evidence of a Bedrock outage. **Needs work:** The observed
response asks for confirmation for some low-risk reviews; plan wording and
application policy remain separate. One successful call establishes neither
reliability nor a latency distribution. **Use again:** Yes, behind explicit
adapters, schema validation, cost authorization and visible provenance.
Evidence: [original 2026-09-12 proof](evidence/bedrock-20260912.json) and
[reviewed output](evidence/bedrock-20260912.log.txt). No new call is represented.

## AWS CodeBuild, CloudFormation, IAM and CloudWatch

**Use:** One temporary managed build executed immutable repository source and
the authorized Bedrock proof. Reviewed infrastructure and IAM scoped the job;
logs preserved the result before verified cleanup. **Worked well:** The single
build succeeded, including 83 tests at that historical source, and the temporary
stack, project, dedicated role and log group were removed. **Onboarding:** Source,
role, configuration and budget were prepared before the single approved run.
**Needs work:** That run spent 288 seconds provisioning and 30 seconds building
(F-004). Surface provisioning progress separately from model latency; its cause
was not established. **Use again:** Yes, for an isolated cloud proof with explicit
cost and cleanup gates. Actual final billing and promotional award remain
unconfirmed. Evidence: the same original proof and F-004; no current hosted
service, general production deployment or repeated-run performance is claimed.

## GitHub, GitHub Actions, Playwright and FFmpeg

**Use:** Public source, reviewed branches/PRs, four CI jobs, real browser
interactions and a captioned recording from the actual application. **Worked
well:** Tests and source-bound artifacts provide a reproducible judge path
without depending on the owner's computer. Desktop/mobile and TLS/recovery
checks run beside the service. **Onboarding:** Repository creation needed a
one-time manual step (F-001); subsequent branch/PR/CI operations were automated.
The separate cloud browser could not reach executor loopback (F-002), so QA
moved to GitHub runners. **Needs work:** Runner media dependencies must be
explicit: missing FFmpeg initially blocked encoding (F-005), then an explicit
install resolved it. CI artifact access is not anonymous public video hosting.
**Use again:** Yes, with pinned actions, declared dependencies and verified
artifact identities. Evidence: [PR #15](https://github.com/Elinfiny/HestiaRelay/pull/15)
and [recording receipt](evidence/release-20260913.json).

## Scope of the feedback

Alexa+ is a guided simulation here; no device onboarding or live Alexa+ service
experience is claimed. AgentCore, Strands, Kiro Crew and SageMaker were not used.
Security scanners and dependency notices are documented in the
[release audit](RELEASE_AUDIT.md); passing its scoped gate is not a zero-CVE or
public-deployment attestation. Tooling friction is kept distinct from feedback
on Amazon runtime services. The final submission should preserve these limits.
