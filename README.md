# HestiaRelay

**A persistent Alexa+ household continuity agent that carries goals across sessions, orchestrates low-risk household work, and stops at consent gates before sensitive actions.**

HestiaRelay is being built for the **Alexa+ track** of the 2026 Amazon Developer Hackathon, with parallel eligibility targets for the **AWS Builder** and **Open Source** mini challenges.

## Core scenario

> “We’re having six people over Friday evening.”

HestiaRelay turns that intent into a durable household workflow: guest count, budget, preferences, reminders, preparation tasks, and proposed purchases remain available across later sessions. Low-risk planning can continue automatically; sensitive operations are surfaced as explicit approval gates.

A follow-up session can add context such as:

> “Remember Ana is allergic to nuts.”

A later session can ask:

> “Are we ready for Friday?”

The goal is continuity, not another single-turn chatbot.

## Hackathon compliance targets

- **Primary track:** Alexa+
- **Runtime surface:** self-hosted MCP server using **Streamable HTTP**
- **MCP requirement:** compatible with the hackathon minimum specification baseline **2025-11-25**
- **AWS Builder target:** Amazon Bedrock at runtime, followed by AgentCore/Strands integration where it materially improves the product
- **Open Source target:** public repository with MIT license and hackathon-window contribution history
- **Submission language:** English

## Architecture

```text
Alexa+ / simulated voice + visual experience
                    │
                    ▼
       MCP over Streamable HTTP
                    │
                    ▼
             HestiaRelay core
        ┌───────────┼────────────┐
        ▼           ▼            ▼
 continuity      risk gate     tool plan
   state                        + evidence
        │           │            │
        └───────────┼────────────┘
                    ▼
           AWS orchestration layer
        Bedrock → AgentCore/Strands
                    │
                    ▼
          allow-listed household tools
```

The bootstrap already contains a real MCP server surface, persistent local continuity state for development, explicit risk classification, consent-gated proposals, and an Amazon Bedrock runtime adapter. Cloud memory and the Alexa+ simulation are subsequent validated milestones.

## MCP tools

The initial MCP server exposes bounded tools for:

- starting or updating a household goal;
- remembering a household preference;
- retrieving a continuity brief across sessions;
- generating a plan with Bedrock when configured, with deterministic fallback otherwise;
- proposing a household action;
- approving or rejecting sensitive proposals.

No tool accepts arbitrary shell commands. Purchase-like or external-account actions are proposals only until explicitly approved, and the bootstrap does not perform a real purchase.

## Local setup

Requirements:

- Python 3.12+
- Git

```bash
git clone https://github.com/Elinfiny/HestiaRelay.git
cd HestiaRelay
python -m venv .venv
```

Activate the environment and install:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

python -m pip install -e ".[dev]"
```

Run the MCP server:

```bash
python -m hestiarelay.server
```

The Streamable HTTP MCP endpoint is available at:

```text
http://127.0.0.1:8000/mcp
```

A plain health endpoint is also exposed at `/health`.

## Optional Amazon Bedrock runtime

Set a model ID and AWS region before launching the server:

```bash
# Windows PowerShell
$env:HESTIA_BEDROCK_MODEL_ID="<your-enabled-bedrock-model-id>"
$env:AWS_REGION="us-east-1"

# macOS/Linux
export HESTIA_BEDROCK_MODEL_ID="<your-enabled-bedrock-model-id>"
export AWS_REGION="us-east-1"
```

Normal AWS credential resolution is used by boto3. Credentials must never be committed to this repository.

## Validation

```bash
ruff check .
pytest --cov=hestiarelay --cov-report=term-missing
```

GitHub Actions runs the same checks on pull requests.

## Evidence-first development

HestiaRelay keeps competition evidence in the repository from the start:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — product and technical boundaries
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) — consent, privacy, and execution risks
- [`docs/SCORING_MATRIX.md`](docs/SCORING_MATRIX.md) — explicit mapping to judging criteria
- [`docs/FRICTION_LOG.md`](docs/FRICTION_LOG.md) — reproducible developer-experience findings for bonus judging
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — gated implementation sequence
- [`AGENTS.md`](AGENTS.md) — repository operating contract for AI-assisted development

## Status

**Bootstrap foundation.** The repository intentionally separates validated foundations from unproven AWS/Alexa+ claims. Features are documented as complete only after implementation and tests prove them.

## License

MIT — see [`LICENSE`](LICENSE).
