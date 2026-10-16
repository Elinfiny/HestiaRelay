# Collection compatibility47 review

Scope: one new guarded import-boundary case, not cleanup45 replay or full pytest.
Test45 infrastructure only: global signal.alarm removed; standalone __main__ owns
its20s timer and explicit optional helper-path argument parsing. Imported/pytest
mode resolves the default helper relative to __file__ inside the unexecuted test
method; module import reads no argv/ENV/helper/private files. Remove unused
math/re/time imports. The functional cleanup scenario AST after its initial path
assignment is byte-structure-equivalent to accepted45. No helper44 edits.

One new47 method compiles/loads the full pinned final45 source as non-__main__ with
correct __file__ and pytest-like argv. Stdlib preloaded before guards. Timer/ENV/
files/private paths/network/SSL/subprocess/helper-import/old TestCase.run guarded.
Unittest loader sees exactly CleanupOwner45 and its one method without running it.
Actual45/helper execution and fakePOST=0. One hostchild20s/parent25s, each output
pipe131072B, complete separately retained stdout/stderr and actual terminal.
Abort/FAIL means no repair/replay47 and no dependent Git writes.

If the exact import-boundary case passes, source-only publication is limited to
one MOD tests/test_nonce_transport45_cleanup.py and two ADDs: this document and
tests/test_transport47_collection.py. New branch review/hestia-collection47-20261016,
sole parent92f4bcec60507c3beafe7b5664ad66f759c938f1. Existing branch46/main/PR26,
helper44/doc45/CI/pyproject and all other source leaves remain unchanged. No PR,
merge, CI event, dispatch, rule/permission change, native POST or new nonce grant.
Rollback requires a separately reviewed new revert; no force/reset/delete.

Historical44 failure and scoped45PASS remain preserved. F46-COLLECTION-1 can only
close for this import boundary after independent review. Helper44 unused os/Path
imports remain a separate LINT gate. This is not full Ruff/pytest, observed native
403 repair or security release. Historical43 attempts stay consumed. All remaining
OS6/Perl/FileTemp/headers/raw164/expiry/provenance/fullregression gates remain OPEN.
