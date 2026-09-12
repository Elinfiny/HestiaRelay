# Contributing

HestiaRelay is being developed during the 2026 Amazon Developer Hackathon. Contributions should preserve the project's competition eligibility, public provenance, and safety model.

## Before changing code

1. Read `AGENTS.md`.
2. Read `docs/ARCHITECTURE.md` and `docs/THREAT_MODEL.md`.
3. Open or reference an issue describing the intended behavior.
4. Keep changes inside this repository; do not copy private-project material.

## Development setup

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Run validation:

```bash
ruff check .
pytest --cov=hestiarelay --cov-report=term-missing
```

## Pull requests

A pull request should include:

- the problem being solved;
- user-visible behavior;
- tests for the change;
- any new AWS/Alexa+/MCP dependency or runtime claim;
- security or consent implications;
- friction-log entry when a real platform/tooling issue was encountered.

Do not merge with failing CI, unresolved high-risk findings, committed secrets, or documentation that claims behavior not proven by the code.
