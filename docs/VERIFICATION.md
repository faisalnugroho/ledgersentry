# VERIFICATION — LedgerSentry live evidence

Status: FILLED from `evidence/live.json` (smoke_complete: true, run finished
2026-09-21 16:05 +0800). Every hash below comes from a real Studionet
transaction receipt; no fabricated values. Contract deployed with
`leader_only=False` (full multi-validator consensus).

## Deployment

- Contract address: `0xD5aD50E3c0672A0D315aadD267Cd2B6a636b33b6`
  ([explorer](https://explorer-studio.genlayer.com/contracts/0xD5aD50E3c0672A0D315aadD267Cd2B6a636b33b6))
- Deploy tx: `0xfc28ae9fb92652e8c70eff2d06907cc8b615b1402aca95472783be57112ad9b8`
- Chain: Studionet (61999), RPC `https://studio.genlayer.com/api`
- Deployed-source guarantee: SHA-256 of the deployed contract code was
  asserted byte-identical to `contracts/ledgersentry.py` at the pinned
  commit `2ecf05c13e6cfe6318ba61a91ef033927c24dc09`
  (source commitment `127000e76a2726d5feaef510d0bb1bf7fe28f14142a26a092ab16c049233df5b`)
- Owner / smoke submitter: `0x8183965AD0A53EebcD1869C93d794733291cfD10`

## Live scenarios (multi-validator consensus, leader_only=False)

| # | Scenario | Expected | Tx hash | Readback |
|---|---|---|---|---|
| 1 | open_audit `ls-clean` (compliant subject) | audit OPEN | `0xbf30da6c0c5437718ec01897637573a8b78b38eee851f9b825eac919b3a6045f` | OPEN, subject SHA-256 committed on-chain |
| 2 | open_audit `ls-violation` (lock list removed) | audit OPEN | `0x55812050cd002fe63d32b6f73598967e1558a03b891980129dcaba7dc7f7e2a7` | OPEN |
| 3 | open_audit `ls-thin` (49-char stub subject) | audit OPEN | `0x5f16d75c8e19a19f2ace0c0b07ca96a56d2a9198f6c3591dab6929325f064d7e` | OPEN |
| 4 | add_evidence x2 on `ls-clean` | digests + URLs appended | `0x08d73a1373e5024f9497d0e54a17fbc6f044dcf1d047b92d7fb6eb9592ba2e42`, `0x11c6623a21d2ff29029cf1862328d0966553183106accdf122d7cb31877ec105` | 2 evidence items on-chain |
| 5 | resolve `ls-clean` | COMPLIANT | `0x31d4473d121bec2530b9e0b4bc92b052d7c790f601e26e093c52093761fc3ce6` | RESOLVED COMPLIANT, 3 grounded citations |
| 6 | resolve `ls-violation` | VIOLATION | `0x9e7ade15583d2c96a0825b3001864a24c1fbc23a0926af4ba5ac86c10982edd8` | RESOLVED VIOLATION, 3 grounded citations |
| 7 | resolve `ls-thin` (unfetchable/thin subject) | INCONCLUSIVE | `0xe4a24b757d54a46c39098ef1b3de070717ec3f59f1aaff19e03bbbaecbe1fab5` | RESOLVED INCONCLUSIVE — fail-closed, zero citations fabricated |
| 8 | open_audit `ls-guard` + open_dispute (1h window) + resolve BEFORE deadline | OPEN, DISPUTED, then revert | open: `0x24a87761e58c0be442a36b24791947a3a471cc400b9c4ebb121e18099d751758` · mark: `0xf70cd386661fccdae231676b62413878fc1f25b9c005d09fe35164404d280102` · early resolve: `0x67855b2787496b1d4dd28afb87b55928916f96682f9e86a2ffe40b20b454ec65` | deadline set on node clock; early resolve reverted; audit still DISPUTED after |
| 9 | open_audit `ls-dispute2` + open_dispute (60s window) + add_dispute_evidence in window | OPEN, DISPUTED + deadline + rebuttal stored | open: `0xbe742e8899f9ff5d6516754c4a4309438501bb8a3fcea845fedb566e79cbaed6` · mark: `0x3ec2d63d214b8312c14962945563217643f0ee1723d26113cac13082622ca5f9` · evidence: `0x6506f56c0addd7f16f0fd041aa4704c20743d25f4a32fcc4fe7ae1e1f9d1cd1a` | DISPUTED, deadline `2026-09-21T08:04:04Z`, rebuttal digest on-chain |
| 10 | resolve `ls-dispute2` AFTER deadline | RESOLVED verdict | `0x994c287b742810b2a0d4a070bd996c6ecabbc2314f5e83718fdd7d29f2d29fc5` | RESOLVED COMPLIANT, rebuttal evidence in the final record |

Note on `steps` history in `evidence/live.json`: the earlier `compliant-*`
and `dispute-*` entries (`0x8747d64693a2bd3da2cf3bdb0a0379ccb7a55ee8d40aac243947c577a4989357`,
`0x7596d6e112385e6f93754c6d651d0d4aad3a408d41ca2e28439089490851fd58`,
`0x767e5d5b649219cabcf5609c6109eb11d842cf319b3e9e4129ce0f4a3fc24906`,
`0x75037e5a8073af57f55eaa07cfdfdc6779862bbbb2307c8b9c4ac05946b053c2`,
`0x112c4bb33bcbb0480e08e09b66aa343787884323c170aa7344dd8d6dd7f03b7e`,
`0x23e27a0a35c30d171414d7583b2429bd211289c81f3fad262f817b3f75020d86`,
`0xab07ddc01784fc26fcc9f23e66359fb8db5d21e97193c31767c802198e458650`)
are from a first partial run against the previous commit pin (`5c541ac…`)
and are superseded by the final run above; they are retained only as an
audit trail.

All final on-chain states were read back via `get_audit` after each receipt
sealed (assertions in `scripts/live_smoke.py`); see `evidence/live.json`
(committed) for full receipts and readbacks. The harness hard-timeouts every
SDK call and retries transient RPC failures; `scripts/live_smoke.py` is the
reproducible driver and never re-sends an uncertain write.

## Test environment results (pre-deploy, this machine)

- pytest tests/ -v : 72 passed (direct mode, GenVM runner v0.3.0-rc7)
- genvm-lint check : ok=true, lint passed=3, validate ok=true, 7 methods

## v1.1 steward-remediation round (September 2026, pre-redeploy)

Steward findings R1 (universal challenge period), R2 (per-requirement
citation validation), R3 (oversized sources resolved incomplete, never
prefix-audited) implemented in `contracts/ledgersentry.py`; direct-mode
suite extended 72 → 94 tests covering pre-deadline resolution, unrelated /
cross-requirement citations, and contradictory-or-oversized sources beyond
the analysis budget. Fresh local evidence for THIS candidate:

- pytest tests/ -q : 94 passed (full output re-executed after the final
  contract/test edits; GenVM runner v0.3.0-rc7 via gltest direct mode)
- genvm-lint check contracts/ledgersentry.py --json : validate.ok = true,
  0 errors, 0 warnings
- frontend: `node --check frontend/app.js` clean; mocked-SDK browser
  integration (`scripts/browser_test.py`) BROWSER_TEST_PASS at 1440 and
  390 widths with the v1.1 record shape (challenge fields, truncated
  manifest flags, requirement-bound citations)
- Live re-deploy + re-smoke on the new source: see the Redeploy section
  (appended after the v1.0 tables below once the new deployment receipt
  exists). v1.0 transaction evidence above remains valid for the contract
  version it exercised (commit `2ecf05c…`) and is retained as history.
