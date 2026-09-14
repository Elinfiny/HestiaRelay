# Main branch protection

Updated 2026-09-14. GitHub ruleset **Protect main** (ID `23281588`) is active
and targets only the default branch. A fresh API readback reports canonical
main `df4d8cf54e37dc674c18350b95e0cd0900e7de12` as `protected: true`.

## Effective rule

The active rule:

- restrict deletions and block force pushes;
- require a pull request before merging, with no mandatory approving review for
  this single-maintainer repository;
- require the four current CI checks from GitHub Actions: `validate`, `browser`,
  `cloud-proof-package` and `container-judge`;
- require branches to be up to date before merging;
- require all review conversations to be resolved; and
- have no bypass actor.

It does not require signed commits, linear history, deployments, code scanning,
code-quality services or a coverage provider that this repository does not
currently emit. Those settings would block legitimate merges without adding a
verified control. Direct restriction of all updates is also unnecessary because
the pull-request and status-check requirements provide the intended gate.

GitHub's saved-ruleset readback confirms an empty bypass list,
`current_user_can_bypass: never`, strict up-to-date checks, and GitHub Actions
integration ID `15368` for all four required checks. The rule was created at
`2026-09-14T12:20:15.271+03:00`; both the ruleset endpoint and branch endpoint
were read back after the save. PR #22 was the first guarded delivery after the
rule was activated. It merged as `df4d8cf54e37dc674c18350b95e0cd0900e7de12`
after exact-head CI passed, and post-merge main CI 34828630607 passed all four
jobs. Issue #16 preserves the provider receipt.
