# VERIFICATION — LedgerSentry live evidence

Status: FILLED from `evidence/live.json` (smoke_complete: true, run finished
2026-09-25 23:20 +0800). Every hash below comes from a real Studionet
transaction receipt; no fabricated values. Contract deployed with
`leader_only=False` (full multi-validator consensus).

## Deployment (current, v1.2 source)

- Contract address: `0x1B0d92c7732e466ee983D71e6f213eDE4Fd1CBac`
  ([explorer](https://explorer-studio.genlayer.com/contracts/0x1B0d92c7732e466ee983D71e6f213eDE4Fd1CBac))
- Deploy tx: `0xeabc63da5f3f1f0f616d26594d0c5c740844bfba7069f6a46f98675f1a41acef`
- Chain: Studionet (61999), RPC `https://studio.genlayer.com/api`
- Deployed-source guarantee: SHA-256 of the deployed contract code was
  asserted byte-identical to `contracts/ledgersentry.py` at the pinned
  commit `0b8c0a5f945763047ddca26a8d924829e20fb949`
- Owner / smoke submitter: `0x8183965AD0A53EebcD1869C93d794733291cfD10`

## Live scenarios (multi-validator consensus, leader_only=False)

| # | Scenario | Expected | Tx hash | Readback |
|---|---|---|---|---|
| 1 | open_audit `ls-clean` (compliant subject, challenge=300) | audit OPEN | `0x9de29f3f72a1ac973c6853184f71af487b2bc9aeec88846019ca757b41e669c5` | OPEN, subject SHA-256 committed on-chain |
| 2 | add_evidence x2 on `ls-clean` | digests + URLs appended | `0xff9e169f623a561f7ed1d377333b48fa57fbc413f86ca870a6a57a6a6b8cf748`, `0xcbf690bb9afabe29c4631f52c8cd04230820dadcb1d1fa799c4aee1785aef57a` | 2 evidence items on-chain |
| 3 | resolve `ls-clean` AFTER challenge deadline | COMPLIANT | `0x456b9f8cb8a13abc0c44cdf8efd6a1fda3c6319c263c62777a352a49c990c59c` | RESOLVED COMPLIANT, labels PASS/PASS/PASS, 3 grounded citations |
| 4 | open_audit `ls-violation` (lock list removed) + resolve after challenge | VIOLATION | open: `0x7714dc01a2f7c897c3077020b2ab44ca9fa4e925700ab090af209bdc3582bc56` · resolve: `0x2002348882a26fe2579656aaae473616a01608368b22b5051e4801fdf9490b1f` | RESOLVED VIOLATION, labels include FAIL, 3 grounded citations |
| 5 | open_audit `ls-thin` (49-char stub subject) + resolve | INCONCLUSIVE | open: `0x6bab3e22643f5f65ef9d84df387d4df5b329be29d994001757130df181302422` · resolve: `0xde91ef17ad8ee033190e6c49ef5dd02a4099200af7f2038720efb193c77ac996` | RESOLVED INCONCLUSIVE — fail-closed, zero citations fabricated |
| 6 | open_audit `ls-guard` + open_dispute (1h window) + resolve BEFORE deadlines | DISPUTED, then revert | open: `0x5dbf457ed9ab130c4cdf848e472356f9a71271e8b4598ecf0ea73d7d994637f2` · mark: `0x57f0bc26aaabcec1af0f1167a46810b8f87d13ba94e9a772e02c0a5e614400aa` · early resolve: `0x066d65b5a76cf06ba21be26825bbc7e4968d5f5a323537f9126318e471920036` | early resolve reverted (guard exercised live); audit still DISPUTED after |
| 7 | open_audit `ls-dispute2` + open_dispute (60s window) + add_dispute_evidence in window | DISPUTED + deadline + rebuttal stored | open: `0x1c79b1e46467f70695dd37944cde7a2ae6ba69533b90cf77922cffcb9b992294` · mark: `0xfed4f0d42d28ba1b25af596d8106cd4a97939c61838715d5e8952cbc887ce97e` · evidence: `0x6c3a6f579d7927b0ce3aa7a04e16192f6938e51b572ef8f557474167e36acef0` | DISPUTED, node-clock deadline, rebuttal digest on-chain |
| 8 | resolve `ls-dispute2` AFTER window + challenge end | RESOLVED verdict | `0xa49b921e9a89979aaca0b325928d11642fbe6cbbdff7ecbc112c251cfd13dbad` | RESOLVED COMPLIANT, rebuttal evidence in the final record |

The harness hard-timeouts every SDK call and retries transient RPC failures;
`scripts/live_smoke.py` is the reproducible driver and never re-sends an
uncertain write. Full receipts and readbacks: `evidence/live.json` (committed).

## Test environment results (pre-deploy, this machine)

- pytest tests/direct -q : 98 passed (direct mode, GenVM runner v0.3.0-rc7)
- genvm-lint check contracts/ledgersentry.py --json : validate.ok = true,
  0 errors, 0 warnings
- frontend: `node --check frontend/app.js` clean; mocked-SDK browser
  integration (`scripts/browser_test.py`) BROWSER_TEST_PASS at 1440 and
  390 widths (v1.1+ record shape)

## Remediation history

- v1.0 (commit `2ecf05c…`, contract `0xD5aD50E…33b6`): initial acceptance
  round; live evidence archived in git history and `evidence/live-v1.0.json`.
- v1.1 (commit `4e82728…`, contract `0x14f5064…fd311`): steward findings R1
  (universal challenge period), R2 (per-requirement citation validation),
  R3 (oversized sources resolved incomplete, never prefix-audited)
  implemented; suite extended 72 → 94. Live smoke exposed a regression: the
  studio model's citations failed the strict v1.1 schema (mandatory
  `requirement` tags), so EVERY live resolution degraded to the fail-safe
  INCONCLUSIVE (`evidence/live-v1.1-partial.json`).
- v1.2 (commit `0b8c0a5…`, contract `0x1B0d92c…CBac`, CURRENT): citation
  requirements are derived by the CONTRACT from quote content (deterministic
  lexical association; model tags never trusted) and labels without their own
  on-topic citation degrade to UNCERTAIN per label instead of poisoning the
  whole audit. Steward requirements R1-R3 unchanged and enforced. Suite
  extended 94 → 98. Live re-deploy + full re-smoke completed on this
  contract: the table above is the evidence for THIS candidate.
