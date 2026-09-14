# Main branch protection

Updated 2026-09-14. GitHub readback at canonical main
`e65c978d9bc9d3f4734e94eee3a330cbae928289` reports `protected: false`, and the
repository ruleset collection is empty. The banner shown on the repository is
therefore accurate; the existing guarded PR discipline is not provider-enforced.

## Intended rule

Create one active branch ruleset named **Protect main** targeting only the
default branch. It should:

- restrict deletions and block force pushes;
- require a pull request before merging, with no mandatory approving review for
  this single-maintainer repository;
- require the four current CI checks: `validate`, `browser`,
  `cloud-proof-package` and `container-judge`;
- require branches to be up to date before merging;
- require all review conversations to be resolved; and
- have no bypass actor.

Do not require signed commits, linear history, deployments, code scanning,
code-quality services or a coverage provider that this repository does not
currently emit. Those settings would block legitimate merges without adding a
verified control. Direct restriction of all updates is also unnecessary because
the pull-request and status-check requirements provide the intended gate.

This document records the prepared control, not an applied state. After the
repository permission change is explicitly confirmed and saved, replace this
paragraph with the ruleset ID, effective-state readback and protected PR-path
verification. Never claim protection from an unsaved form or banner dismissal.
