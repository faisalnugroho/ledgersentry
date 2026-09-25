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
Contract: https://explorer-studio.genlayer.com/contracts/0xD5aD50E3c0672A0D315aadD267Cd2B6a636b33b6
Verification: https://github.com/faisalnugroho/ledgersentry/blob/main/docs/VERIFICATION.md
Audit: https://github.com/faisalnugroho/ledgersentry/blob/main/docs/AUDIT.md

## Demonstration evidence

(one explorer tx link per scenario — all live on Studionet, full
multi-validator consensus; see docs/VERIFICATION.md for readbacks:)

- COMPLIANT resolution:
  https://explorer-studio.genlayer.com/tx/0x31d4473d121bec2530b9e0b4bc92b052d7c790f601e26e093c52093761fc3ce6
- VIOLATION resolution (FAIL label):
  https://explorer-studio.genlayer.com/tx/0x9e7ade15583d2c96a0825b3001864a24c1fbc23a0926af4ba5ac86c10982edd8
- INCONCLUSIVE (dead subject, fail-closed):
  https://explorer-studio.genlayer.com/tx/0xe4a24b757d54a46c39098ef1b3de070717ec3f59f1aaff19e03bbbaecbe1fab5
- Dispute opened + resolved after window:
  mark https://explorer-studio.genlayer.com/tx/0x3ec2d63d214b8312c14962945563217643f0ee1723d26113cac13082622ca5f9
  resolve https://explorer-studio.genlayer.com/tx/0x994c287b742810b2a0d4a070bd996c6ecabbc2314f5e83718fdd7d29f2d29fc5
- Dispute evidence appended during window:
  https://explorer-studio.genlayer.com/tx/0x6506f56c0addd7f16f0fd041aa4704c20743d25f4a32fcc4fe7ae1e1f9d1cd1a

## Honest scope notes

New work, week of September 21, 2026; different domain from the author's
previous escrow/license/commit/wallet/grant/recall/identity contributions.
No real-world audits or users claimed; examples are synthetic. First-party
audit only. Single dispute round per audit; a fresh audit is the escalation
path. No payment, no token, no mainnet-readiness claim.

The owner submits this Project manually. No login, signature or submission
action is performed by automation.
