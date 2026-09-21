# VERIFICATION — LedgerSentry live evidence

Status: TEMPLATE — filled by scripts/deploy_studionet.py + scripts/live_smoke.py
during the Studionet deployment round. Every hash below must come from a real
transaction receipt; no fabricated values.

## Deployment

- Contract address: PENDING
- Deploy tx: PENDING
- Chain: Studionet (61999)
- Deployed code hash: PENDING

## Live scenarios (multi-validator, leader_only=False)

| # | Scenario | Expected | Tx hash | Readback |
|---|---|---|---|---|
| 1 | open_audit (compliant subject) | audit OPEN | PENDING | PENDING |
| 2 | open_audit (violating subject) | audit OPEN | PENDING | PENDING |
| 3 | open_audit (thin subject) | audit OPEN | PENDING | PENDING |
| 4 | add_evidence x2 | evidence appended | PENDING | PENDING |
| 5 | resolve compliant audit | COMPLIANT | PENDING | PENDING |
| 6 | resolve violating audit | VIOLATION | PENDING | PENDING |
| 7 | resolve thin-subject audit | INCONCLUSIVE | PENDING | PENDING |
| 8 | open_dispute + add_dispute_evidence | DISPUTED + deadline set | PENDING | PENDING |
| 9 | resolve before deadline | reverted (expected) | PENDING | PENDING |
| 10 | resolve after deadline | RESOLVED verdict | PENDING | PENDING |

## Test environment results (pre-deploy, this machine)

- pytest tests/ -v : 72 passed (direct mode, GenVM runner v0.3.0-rc7)
- genvm-lint check : ok=true, lint passed=3, validate ok=true, 7 methods
