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
requirements; anyone appends hash-committed evidence; every audit carries an
enforceable on-chain challenge period plus a permissionless dispute window
with node-clock deadlines protecting the subject owner. Validators
independently re-fetch every source, verify byte commitments, and re-derive
the result: the model only returns per-requirement PASS/FAIL/UNCERTAIN labels
with verbatim grounded citations; the contract re-associates every citation
by content and derives COMPLIANT / VIOLATION / INCONCLUSIVE itself. Oversized
sources resolve incomplete, never prefix-audited. Includes a usable
dashboard, 98 direct-mode tests, GenVM validation, first-party security
review, real multi-validator transactions and browser-to-chain verification.
Testnet prototype: digests prove integrity not truth, participation is not
Sybil-resistant, and LLM labels can be wrong.

## Links

Repository: https://github.com/faisalnugroho/ledgersentry
Dashboard: https://faisalnugroho.github.io/ledgersentry/
Contract: https://explorer-studio.genlayer.com/contracts/0x1B0d92c7732e466ee983D71e6f213eDE4Fd1CBac
Verification: https://github.com/faisalnugroho/ledgersentry/blob/main/docs/VERIFICATION.md
Audit: https://github.com/faisalnugroho/ledgersentry/blob/main/docs/AUDIT.md

## Demonstration evidence

(one explorer tx link per scenario — all live on Studionet against the
CURRENT contract `0x1B0d92c…CBac`, full multi-validator consensus; see
docs/VERIFICATION.md for readbacks:)

- COMPLIANT resolution (after challenge period):
  https://explorer-studio.genlayer.com/tx/0x456b9f8cb8a13abc0c44cdf8efd6a1fda3c6319c263c62777a352a49c990c59c
- VIOLATION resolution (FAIL label):
  https://explorer-studio.genlayer.com/tx/0x2002348882a26fe2579656aaae473616a01608368b22b5051e4801fdf9490b1f
- INCONCLUSIVE (dead subject, fail-closed):
  https://explorer-studio.genlayer.com/tx/0xde91ef17ad8ee033190e6c49ef5dd02a4099200af7f2038720efb193c77ac996
- Early resolution reverted by the challenge/dispute guard:
  https://explorer-studio.genlayer.com/tx/0x066d65b5a76cf06ba21be26825bbc7e4968d5f5a323537f9126318e471920036
- Dispute evidence appended during window:
  https://explorer-studio.genlayer.com/tx/0x6c3a6f579d7927b0ce3aa7a04e16192f6938e51b572ef8f557474167e36acef0
- Dispute resolved after window:
  https://explorer-studio.genlayer.com/tx/0xa49b921e9a89979aaca0b325928d11642fbe6cbbdff7ecbc112c251cfd13dbad

## Honest scope notes

New work, week of September 21, 2026 (v1.2 remediation September 25, 2026);
different domain from the author's previous escrow/license/commit/wallet/
grant/recall/identity contributions. No real-world audits or users claimed;
examples are synthetic. First-party audit only. Single dispute round per
audit; a fresh audit is the escalation path. No payment, no token, no
mainnet-readiness claim.

The owner submits this Project manually. No login, signature or submission
action is performed by automation.
