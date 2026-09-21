# SECURITY REVIEW — LedgerSentry (first-party)

Scope: `contracts/ledgersentry.py` as committed. Static review plus the
adversarial cases in `tests/direct/`. First-party review, not an external
audit. No offensive reproduction against live systems was performed or needed.

## Threat model

Adversaries: a subject owner wanting a clean audit of a non-compliant
artifact; a disputant wanting to force VIOLATION on a compliant artifact; a
malicious or fooled leader validator proposing fabricated results; a spammer
exhausting storage. Assets: verdict integrity, window fairness, bounded
resources.

## Findings and controls

| # | Threat | Control | Test |
|---|---|---|---|
| S1 | LLM outputs fabricated PASS | PASS hard-requires a verbatim subject citation present in the fetched bytes (`pass_without_subject_citation`), and subject must be non-empty (`pass_without_subject`) | test_pass_without_subject_citation_rejected, test_dead_subject_never_passes |
| S2 | Subject swapped after audit opens | SHA-256 commitment at write time; fetch with different bytes → unusable source | test_tampered_subject_detected |
| S3 | Dead/404/thin subject passes | fetch must be 200 + digest-matched + ≥50 chars; else unusable | test_subject_fetch_failure_fails_closed, test_dead_subject_never_passes |
| S4 | COMPLIANT with missing evidence | COMPLIANT requires zero unusable committed sources | test_unfetched_dispute_cannot_force_pass |
| S5 | Model picks the verdict | model `verdict` field ignored; contract derives from labels | test_llm_cannot_pick_verdict_field |
| S6 | Lying leader validator | validator re-fetches fresh bytes, compares (verdict, labels, manifest), re-normalizes leader record | test_forged_leader_label_rejected, test_forged_leader_verdict_rejected, test_forged_manifest_rejected, test_divergent_fetch_rejected |
| S7 | Manipulated clock (client-supplied time) | deadline from `gl.message_raw["datetime"]` — assigned by the executing node, never sent by the client | test_resolve_blocked_during_window, test_resolve_allowed_after_window |
| S8 | Rushed resolution (dispute grief) | `response_window_active` guard is BEFORE any resolution path | test_resolve_blocked_during_window |
| S9 | Budget starvation of original evidence by dispute spam | category-split budgets from metadata, hard cap asserted at module load, dispute capped at 3 items | test_budget_invariant_holds, test_budget_order_in_prompt |
| S10 | Storage exhaustion | ≤100 audits, ≤4+3 evidence items, bounded field lengths, JSON ≤4000 chars | test_registry_capacity, test_evidence_capacity, test_dispute_evidence_capacity |
| S11 | Injection via URLs/requirements | pinned-URL allowlist (scheme/host/commit/path/extension), path segment checks, prompt declares all DATA as non-instructional | test_url_allowlist |
| S12 | Replay/duplicate evidence | per-category duplicate-digest rejection | test_add_evidence_lifecycle |
| S13 | State confusion across lifecycle | explicit status machine (OPEN/DISPUTED/RESOLVED) with machine-readable reverts | test_state_machine_categories, test_double_dispute_and_resolution_terminality |

## Residual risks (accepted, disclosed)

- **Consensus-invalid leader proposals** in a real multi-validator network
  cause the tx to fail rather than a verdict; retry semantics are the node's,
  not the contract's.
- **Sybil evidence**: any address may append evidence; quality is enforced by
  commitment + grounding, not by reputation.
- **Truth vs integrity**: a hash proves the bytes match; it cannot prove the
  artifact is honest.
- **Node-time granularity**: `datetime` is ISO with microsecond precision from
  the executing node; a one-second race at the deadline boundary resolves in
  favor of resolution (deadline is inclusive).

## Verdict

No blocking findings. The fail-closed property holds on every path exercised:
every model failure shape, every source failure shape, and every forged-leader
shape tested degrades to INCONCLUSIVE or False, never to a false COMPLIANT/VIOLATION.
