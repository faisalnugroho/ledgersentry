# Portal submission draft — submit manually as Project

Title: LedgerSentry — on-chain compliance audit desk
Category: Project
Suggested primary tag: Auditing
Suggested secondary tags: Compliance; Token Disclosures
Network: studio (Studionet, chain 61999)

## Description (under 1000 characters)

LedgerSentry audits published text artifacts (token statements, treasury
policies) against structured natural-language requirements on GenLayer. An
owner opens an audit with a commit-pinned subject (SHA-256 committed) and 3-8
requirements; anyone appends hash-committed evidence; a permissionless
dispute window with an on-chain, node-clock deadline protects the subject
owner with guaranteed response time. Validators independently re-fetch every
source, verify byte commitments, and re-derive the result; the model only
returns per-requirement PASS/FAIL/UNCERTAIN labels with verbatim grounded
citations while the contract derives COMPLIANT / VIOLATION / INCONCLUSIVE.
Includes a usable dashboard, 72 direct-mode tests, GenVM validation,
first-party security review, real multi-validator transactions and
browser-to-chain verification. Testnet prototype: digests prove integrity
not truth, participation is not Sybil-resistant, and LLM labels can be wrong.

## Links

Repository: https://github.com/faisalnugroho/ledgersentry
Dashboard: https://faisalnugroho.github.io/ledgersentry/
Contract: (fill after deploy — explorer-studio contract URL)
Verification: https://github.com/faisalnugroho/ledgersentry/blob/main/docs/VERIFICATION.md
Audit: https://github.com/faisalnugroho/ledgersentry/blob/main/docs/AUDIT.md

## Demonstration evidence

(fill after live smoke — one explorer tx link per scenario:)

- COMPLIANT resolution:
- VIOLATION resolution (FAIL label):
- INCONCLUSIVE (dead subject, fail-closed):
- Dispute opened + resolved after window:
- Dispute evidence appended during window:

## Honest scope notes

New work, week of September 21, 2026; different domain from the author's
previous escrow/license/commit/wallet/grant/recall/identity contributions.
No real-world audits or users claimed; examples are synthetic. First-party
audit only. Single dispute round per audit; a fresh audit is the escalation
path. No payment, no token, no mainnet-readiness claim.

The owner submits this Project manually. No login, signature or submission
action is performed by automation.
