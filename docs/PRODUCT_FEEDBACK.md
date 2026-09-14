# What the tools were like to build with

These notes describe work recorded in this public repository. They are prepared
for the competition feedback field, which has not been submitted. An isolated
successful run is useful evidence, but it is not a reliability benchmark.
The [friction log](FRICTION_LOG.md) contains the reproducible incidents.

## Amazon services and SDK

| Tool | Use and onboarding | What worked | What needs work | Use again? |
| --- | --- | --- | --- | --- |
| Amazon Bedrock Runtime / Converse | Offline adapter tests came before one approved live invocation. | The real adapter returned a plan with explicit provider and model provenance. | A single response cannot establish consistency; advice still needs application validation. | Yes, behind the same bounded adapter. |
| Amazon Nova Micro | The model was selected for one small fictional household plan. | That call used 222 input and 230 output tokens and took 1,114.44 ms. | Some low-risk review wording asked for confirmation; model advice must not become authorization policy. | Yes, for further evaluated planning, not automatic sensitive actions. |
| boto3 / botocore | Standard region/model configuration and a dedicated role served the Converse adapter. | The same adapter is exercised with mocks and the historical real response. | Credential resolution can add delay; errors need redaction and visible fallback. | Yes, with bounded timeouts and no hidden retries. |
| AWS CodeBuild | One temporary build checked out immutable public source and ran the proof. | It passed 83 tests at that historical source and performed the intended single call. | Provisioning took 288 seconds versus 30 seconds building; show these separately from model latency (F-004). | Yes, for isolated cloud proofs with cleanup. |
| AWS CloudFormation | A reviewed template defined the temporary project, role and logs. | Resource creation did not itself start inference; removal was verified. | Small proofs still require careful source/role binding and cleanup accounting. | Yes, when the repeatable setup justifies a stack. |
| AWS IAM | One dedicated CodeBuild role scoped the approved operation. | The proof used the reviewed role and model scope. | A successful request is not a complete permission audit; broader deployment needs a separate review. | Yes, with explicit resource/action boundaries. |
| Amazon CloudWatch Logs | The temporary build exported its evidence before log-group removal. | The original call output and build result were preserved. | Logs must be checked for sensitive data before publication; retention is not free by assumption. | Yes, with deliberate retention and export. |
| AWS Core plugin | Operation discovery supported the cloud proof workflow. | The required path became available and the controlled proof completed. | Discovery was unavailable in an earlier session (F-003); that was not a demonstrated Bedrock outage. | Yes, after verifying the actual capabilities available in the session. |

The [September 12 receipt](evidence/bedrock-20260912.json) and
[reviewed output](evidence/bedrock-20260912.log.txt) preserve the original source,
usage and cleanup. No new AWS execution occurred during this presentation review.
Final billing and the requested promotional-credit award are not established here.

## Application and interoperability

| Tool | Use and onboarding | What worked | What needs work | Use again? |
| --- | --- | --- | --- | --- |
| Python / standard library | A small typed package contains state, policy, service and transports. | Domain behavior can be tested independently of a browser or AWS. | Setup still requires the documented runtime; this is not a packaged consumer app. | Yes, for a small inspectable service. |
| SQLite | One persistent file holds household state, history and consent. | Separate sessions and actual process/container recreation recover the same context. | One worker and one fictional household are the current contract; production identity and tenancy remain separate work. | Yes, for this prototype and controlled single-instance use. |
| Pydantic | Domain and provider-response models validate structured inputs. | Malformed data fails at explicit boundaries. | Valid structure does not prove food safety or model correctness. | Yes, alongside semantic policy checks. |
| MCP Python SDK / Streamable HTTP | The server and real TCP clients share the household service. | Three sessions negotiate protocol 2025-11-25 and recover the same state. | Local transport interoperability does not supply remote authorization. | Yes, for bounded tools whose effects remain in the domain. |
| MCP Inspector 2.6.0 | The container proof launches the pinned CLI after the server starts. | Initialization, tool listing and an actual tool call pass. | CLI success does not certify every MCP client. | Yes, alongside the independent SDK smoke test. |
| Starlette / Uvicorn | The existing MCP application serves the API and static browser app. | One service prevents a disconnected demonstration backend. | Authentication, origin checks and TLS still require application controls; a known AnyIO deprecation warning is tracked. | Yes, with the boundary tests retained. |
| HTML / CSS / JavaScript | Packaged assets use native controls and a same-origin API. | The dinner story, context and decisions fit desktop and 390px layouts. | Guided sentence patterns are intentionally narrower than open conversation. | Yes; keeping the UI small makes its behavior easier to inspect. |

## Development, tests and delivery

| Tool | Use and onboarding | What worked | What needs work | Use again? |
| --- | --- | --- | --- | --- |
| ChatGPT / Codex | AI-assisted implementation, editorial drafts, diagnosis and review were checked against source and test output. | It helped keep code, evidence and documentation together. | Draft wording sometimes exposed internal approval language; factual and editorial review remains necessary. | Yes, with explicit authority and readbacks; no claim of unaided authorship. |
| Git / GitHub | Public MIT source, feature branches and reviewed PRs preserve history. | Exact commit identities tie results to implementation. | Initial repository creation required a manual step (F-001); provider-enforced `Protect main` is now active for the default branch. | Yes, retaining guarded PR merges and public evidence. |
| GitHub plugin | Repository reads and Git-object/PR operations support cloud-first work. | Source and final state can be reconciled without the creator's PC. | A response error may leave the mutation outcome uncertain (F-007); read back before acting again. | Yes, with idempotent reconciliation. |
| GitHub Actions | Four jobs validate the application, browser, container and cloud-proof package. | Separate artifacts preserve reproducible results. | Two orphaned queued runs needed Support reconciliation (F-009); a queued run is not a running test. | Yes, with bounded recovery and no duplicate retries. |
| pytest / pytest-cov / coverage.py | Domain, adapter, security and real-process regressions run together. | The reviewed baseline has 150 tests and 98.11% application coverage. | Coverage measures exercised statements, not complete correctness or user impact. | Yes, prioritizing consequential behavior over a cosmetic 100%. |
| HTTPX2 | Tests exercise HTTP requests and boundary failures against the service. | Malformed headers and API behavior can be tested directly. | It complements rather than replaces a real browser. | Yes, for transport-focused checks. |
| Ruff | Repository lint is a fast pre-commit and CI gate. | It catches formatting, imports and static Python errors. | It cannot verify consent semantics or claims in prose. | Yes, beside behavioral tests. |
| Playwright / Chromium | CI drives the real app at desktop and mobile widths and records the demonstration. | Reload, consent, TLS and responsive checks produce inspectable evidence. | The separate cloud browser cannot reach runner loopback (F-002); YouTube's bot gate blocked its separate hosted playback check (F-010). | Yes, while keeping browser QA distinct from public playback. |
| FFmpeg / ffprobe | Real captured frames receive captions and, in this review, a separate narration track. | Encoding is reproducible and stream dimensions/duration are measurable. | The first runner lacked FFmpeg (F-005); media dependencies must be declared. | Yes, with source hashes and frame checks. |
| Docker | A non-root, read-only container runs the same service with a persistent volume. | Recreation and backup/restore preserve household state. | Image advisories need current reachability review; a container is not proof of safe public hosting. | Yes, within the documented deployment contract. |
| pip / setuptools / build | Package metadata and pinned proof/runtime inputs support fresh installs and wheels. | CI validates the installed package and packaged static assets. | Broad development ranges can resolve differently later; release inventories are necessary. | Yes, with separate release locks and advisory checks. |
| cfn-lint | CI validates the cloud-proof template without deploying it. | Template mistakes can be caught without AWS costs. | Static validation cannot establish live account permission or model access. | Yes, before any separately authorized cloud run. |
| pip-audit / npm audit | Python and Inspector dependencies are checked against published advisories. | Reports retain exact package/version findings. | No finding is evidence only for that database and date, not future safety. | Yes, with a fresh release check. |
| Trivy | The actual container is scanned and receives an SBOM/license inventory. | Raw findings remain visible beside narrow applicability decisions. | Unfixed package CVEs still need source/control analysis; blanket dismissal would be misleading. | Yes, with expiring reviewed exceptions. |
| Gitleaks | Full Git history and exported artifacts are scanned with redacted output. | Source and evidence are checked before publication. | An exact historical hash false positive needs a narrow entry; do not generalize it to secrets. | Yes, with history and artifact scans retained. |
| YouTube Studio | One accepted 1:28 recording was published with English captions. | The creator confirmed complete signed-out playback in Brave. | Browser mutation responses can time out; saved metadata needs an independent readback. Text URLs need channel verification to be clickable. | Yes, using the existing public upload until a new exact candidate is accepted. |

## Narration authoring

Kokoro-82M with the stock `af_heart` voice, the ONNX conversion,
`kokoro-onnx`, ONNX Runtime, Phonemizer/eSpeak NG, NumPy and SoundFile form a
separate authoring environment. Onboarding used public pinned model files and
checksums, with CPU inference and no speech-service account. The twelve scenes
can be generated and measured independently. A timing check caught an overlong
sentence before encoding; shortening it kept the narration conversational.
These tools are useful again for inspectable narration, provided voice rights,
pronunciation, captions and timing are reviewed. This voice is synthetic;
it is not Alexa, a cloned voice or the creator's recorded voice.
See [reproduction and notices](NARRATION_GUIDE.md).

Alexa+ is simulated; no live device onboarding experience is claimed.
AgentCore, Strands, SageMaker and Kiro Crew were not used. Transitive dependency
licenses belong in the inventory; this feedback does not invent direct user
experience for each underlying package.
