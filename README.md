# LedgerSentry

Intelligent Contract for on-chain **compliance auditing of published text
artifacts** on GenLayer (Studionet testnet). An owner opens an audit with a
commit-pinned public subject and a structured requirement list; anyone may
append hash-committed evidence; a permissionless dispute window with an
on-chain deadline protects the subject owner; and a consensus-backed LLM
evaluation derives a final verdict — **COMPLIANT**, **VIOLATION**, or
**INCONCLUSIVE** — that the contract, never the model, decides.

Live demo: https://faisalnugroho.github.io/ledgersentry/ (deployment links in
`frontend/deployment.json`).

## The trust problem

Token issuers, DAOs and public teams publish disclosure artifacts ("token
statement", "emissions report", "treasury policy") whose compliance with
stated requirements is exactly the kind of judgment a deterministic contract
cannot make and a single centralized auditor must be trusted for. LedgerSentry
turns that audit into a GenLayer primitive: validators independently re-fetch
the same hash-pinned sources and re-derive the same verdict before any result
is accepted.

## Why this is a meaningful GenLayer use case

- **Judgment, not classification** — the model interprets each natural-language
  requirement against the artifact and evidence; `if/else` cannot do this.
- **LLM labels, contract derives** — the model returns only per-requirement
  PASS/FAIL/UNCERTAIN labels with verbatim grounded citations. The verdict is
  a pure contract function: any FAIL → VIOLATION, any UNCERTAIN → INCONCLUSIVE,
  all PASS with every source verified → COMPLIANT.
- **Real on-chain consequence** — terminal on-chain status with an immutable
  auditable record; dispute deadline computed from the node-assigned clock.
- **Independently verifiable evidence** — every source is a commit-pinned
  `raw.githubusercontent.com` URL whose SHA-256 digest is committed at write
  time; validators re-fetch and re-check every byte.
- **Deterministic gates clamp the model** — the hard gate `pass_without_subject_citation`
  rejects any PASS not grounded in the subject; the grounding clamp treats a
  fetched subject thinner than 50 chars as unusable; a definitive COMPLIANT
  requires *every* committed source to be present and verified. A fooled or
  hallucinating model cannot produce a clean audit.

## Dispute path (first-class from v1)

- Anyone may dispute an OPEN audit; the record becomes DISPUTED with
  `dispute_deadline = now + window` from the **node-assigned** (non-manipulable)
  timestamp, parsed with pure integer math (Hinnant `days_from_civil`).
- `resolve()` is permissionless but **reverts while the window is active** — a
  guaranteed minimum answering period, not a submission cutoff: dispute
  evidence stays acceptable until resolution; later items remain
  hash-committed and auditable.
- Blank dispute openings are allowed (the subject always exists; dispute
  evidence itself is rejected when empty per call).
- Fair fetch budgets are split by category from record metadata — subject 3000
  chars, originals ≤3000 each (≤12000 total), dispute items ≤2000 each (≤6000
  total), 21000 hard cap asserted at module load — so appending dispute items
  can never starve the original evidence.

## Honest scope

- Text artifacts only; a digest proves **integrity, not truth** — a self-consistent
  lie commits and audits as clean.
- Open participation is not Sybil-resistant.
- LLM labels can be wrong; INCONCLUSIVE is a first-class outcome.
- One dispute round per audit; escalation means opening a fresh audit.
- First-party security review only (`docs/AUDIT.md`), not an external audit.
- Testnet prototype: no funds, no payments, no token anywhere.

## Repository layout

```
contracts/ledgersentry.py   Intelligent Contract (GenVM, gl.Contract)
tests/direct/               72 real GenVM direct-mode tests (web/LLM mocked)
frontend/                   Static dashboard (GitHub Pages, testnet boundary)
scripts/                    Deploy + live smoke + readback (genlayer-py)
docs/                       PLAN, SPEC_REVIEW, AUDIT, VERIFICATION, SUBMISSION_DRAFT
```

## Development

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v        # 72 tests
genvm-lint check contracts/ledgersentry.py  # static GenVM validation
```

See `docs/PLAN.md` for the design contract and `docs/VERIFICATION.md` for
live transaction evidence.
