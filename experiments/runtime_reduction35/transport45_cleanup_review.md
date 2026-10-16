# Transport45 exact cleanup-case revalidation

Private source-only additions; no edits to 44 and no native activation.
Only one new method/scenario. Explicit expectation correction: CLOSE_RETURN from
old44 test175 is replaced by CONNECTION_CLOSE in independent test45, because
NativeHTTPS.close catches the connection-owner OSError and returns that label.
Wrapper CLOSE_RETURN denotes a different case, which is not tested here.

The identical fake403 body is retained by identity. Primary HTTP_STATUS/ValueError
and original cleanup OSError remain separate; consumed=true/stateUNKNOWN,
one connection construction, one fake POST and one connection close attempt.
Fake timely clock, synthetic TLS context, no CA/network/DNS/credentials/model/spend.
No old suite is imported or executed; late/incomplete/detached cases not repeated.
Helper44 stays byte-identical13399B/SHA256
bcf3fc19fe7e3f24c99adf0b92be7d0301a7ed9306ccd78fd9325d64fab2d066.

Immutable source locator: carrier44 libfile_38f9ab001fcc81918fc6c2550baba772@0,
file_0000000062e8820a881630ef4b0b52e9,
rawSHA256 d780474e082fe596507f6a5b061579d46e61e5e28069eb59838b6434b0378cf4,
selfSHA256 e8ba5511732d8381bc8dfd6b7b624b0b7465698d44509c0b8b04289c151e91ef,
selector sources[path=experiments/runtime_reduction35/consume_once44.py].content.
Carrier44/helper/history are not duplicated in carrier45.

Capture: single child20s/parent25s, two separately retained pipes131072 bytes each,
actual exit and stdout/stderr lengths/hashes. Abort means no repair/replay45.
PASS closes only F44-ASSERT-1 exact scenario, never rewrites failed44 or proves
native403 repair/full regression/security release. Git/PR26/workflows unchanged;
old43 POST/event/job consumed. New native activation requires a distinct new nonce,
protection/budget/authority, not admitted here.

Reversible additions: tests/test_nonce_transport45_cleanup.py and this document
both have ABSENT preimages. Rollback discards those private additions; source44,
provider refs/rulesets and historical receipts remain intact.
