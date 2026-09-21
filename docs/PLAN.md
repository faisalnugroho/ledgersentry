# LedgerSentry — Project build, September 2026

Scope: complete testnet project for Portal submission (Builder → Intelligent
Contracts). No real funds, testnet only. New domain: compliance auditing of a
published artifact against a natural-language requirement set — not
grant/duplicate allocation (GrantWeave), not escrow adjudication
(EscrowAdjudicator/MilestoneJudge), not code/license/wallet forensics
(CommitScope/TokenScope/TrustReconciler), not content recall (RecallShield),
not identity (GenDid).

Architecture: an owner opens an audit with a mandatory commit-pinned public
subject (raw.githubusercontent.com/<o>/<r>/<40-char SHA>/<path>.md|txt,
SHA-256 exact body), a structured requirement list (3–8 natural-language
requirements) and a bounded dispute window (60 s–14 days, enforced on-chain
from node-assigned time). Anyone may append up to 4 original evidence items
(commit-pinned, digest-verified) while OPEN. Anyone may open a dispute: the
record becomes DISPUTED with response_deadline = now + window, and up to 3
dispute evidence items may be appended by any address. resolve() is
permissionless but only proceeds once the deadline has passed — a guaranteed
minimum answering period. Adjudication fetches subject + evidence with fair,
category-split budgets (subject ≤3000 chars, each original ≤3000, total
original ≤12000, each dispute item ≤2000, total dispute ≤6000, hard total
≤21000 asserted at module level), verifies every SHA-256 byte commitment,
then asks the model ONLY for per-requirement labels PASS/FAIL/UNCERTAIN with
verbatim 20–400-char citations from fetched sources; PASS must cite source 0
(the audited subject). The CONTRACT derives the verdict as a pure function:
any FAIL → VIOLATION, any UNCERTAIN → INCONCLUSIVE, else COMPLIANT. Missing,
unfetched, oversized or tampered sources can never produce PASS; subject
unavailability fails closed to INCONCLUSIVE. The validator re-fetches,
re-derives, compares stable substance (verdict, label sequence, evidence
manifest) and re-normalizes the leader's full record against fresh bytes.
Terminal records are immutable; no money moves anywhere in v1.

Shared API (all writes return None; views JSON string):
open_audit(audit_id, title, subject_uri, subject_digest, requirements_json, window_seconds)
add_evidence(audit_id, url, digest)            # ORIGINAL category, OPEN only
open_dispute(audit_id)                         # OPEN → DISPUTED, sets deadline
add_dispute_evidence(audit_id, url, digest)    # DISPUTE category, DISPUTED only
resolve(audit_id)                              # permissionless, after deadline
get_audit(audit_id) -> str
list_audits() -> str (JSON list of IDs)
get_audit returns {id,title,owner,status,subject,requirements,window,
dispute_deadline,evidence:[{index,url,digest}],dispute:[{index,url,digest}],result}.
Statuses OPEN, DISPUTED, RESOLVED. Verdicts COMPLIANT, VIOLATION, INCONCLUSIVE.

Dispute path first-class from v1 (the known steward checklist): blank
dispute opening allowed (original evidence always exists; subject mandatory),
dispute evidence rejected when empty per call, response window enforced
on-chain before resolution, fair fetch budget split by category allocated
from metadata not array position, tests for empty evidence, immediate
resolution, and window-exhaustion ordering.

Honest limits: text artifacts only; digest proves integrity not truth;
open participation is not Sybil-resistant; LLM labels can be wrong; window
uses node time (non-manipulable, assigned by the executing node). No
identity proof, no payment, no protocol-level appeal beyond the single
dispute window; a fresh audit is the escalation path.

Workstreams:
1. Contract + real gltest Direct-mode suite with adversarial cases.
2. Static functional dashboard, fresh testnet burner, SDK writes/readback,
   responsive and clear testnet boundary.
3. Spec review + security review, regressions, actual test/lint runs.
4. Studionet deployment + live smoke with per-scenario transaction hashes.
5. Public repository/Pages, README/audit/submission draft, evidence bundle.

No fabricated test output. Portal submission is performed by the owner.
