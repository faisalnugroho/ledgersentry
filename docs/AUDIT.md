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
| S1b | PASS/FAIL propped by an unrelated requirement's citation | every citation carries a `requirement` index; a PASS/FAIL for requirement i needs ≥1 citation whose verbatim quote lexically relates to requirement i's OWN text (`label_without_related_citation`, deterministic word-overlap ≥1 non-generic word) | test_label_backed_by_unrelated_requirement_citation_rejected, test_cross_requirement_citation_cannot_support_label, test_fail_label_also_needs_related_citation |
| S2 | Subject swapped after audit opens | SHA-256 commitment at write time; fetch with different bytes → unusable source | test_tampered_subject_detected |
| S3 | Dead/404/thin subject passes | fetch must be 200 + digest-matched + ≥50 chars; else unusable | test_subject_fetch_failure_fails_closed, test_dead_subject_never_passes |
| S3b | Oversized source audited as a prefix (partial-context verdict) | a source longer than its category budget is NEVER decoded/audited: the slot is resolved INCOMPLETE (`truncated: true`, bytes 0) and the verdict fails closed to INCONCLUSIVE even if the model quotes in-prefix text | test_oversized_subject_resolved_incomplete_never_prefix_audited, test_oversized_evidence_resolved_incomplete, test_exact_budget_source_audited_in_full |
| S4 | COMPLIANT with missing evidence | COMPLIANT requires zero unusable committed sources (including unresolvable/incomplete ones) | test_unfetched_dispute_cannot_force_pass |
| S5 | Model picks the verdict | model `verdict` field ignored; contract derives from labels | test_llm_cannot_pick_verdict_field |
| S6 | Lying leader validator | validator re-fetches fresh bytes, compares (verdict, labels, manifest), re-normalizes leader record incl. citation↔requirement binding | test_forged_leader_label_rejected, test_forged_leader_verdict_rejected, test_forged_manifest_rejected, test_forged_citation_requirement, test_divergent_fetch_rejected |
| S7 | Manipulated clock (client-supplied time) | deadlines from `gl.message_raw["datetime"]` — assigned by the executing node, never sent by the client | test_resolve_blocked_during_window, test_resolve_allowed_after_window, test_open_audit_writes_immutable_challenge_deadline |
| S8 | Rushed resolution (dispute grief) | universal challenge period (`challenge_period_active`) PLUS the dispute response window (`response_window_active`) both guard BEFORE any resolution path | test_resolve_before_challenge_deadline_reverts, test_dispute_restarts_full_window_after_challenge_expiry, test_resolve_blocked_during_window |
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
- **Lexical ≠ semantic**: the per-requirement citation gate is a deterministic
  word-overlap heuristic; an on-topic but cherry-picked quote can still pass
  it, and heavily paraphrased requirements may reject honest citations
  (the model then fail-closes to INCONCLUSIVE — safe, less usable).
- **Node-time granularity**: `datetime` is ISO with microsecond precision from
  the executing node; a one-second race at the deadline boundary resolves in
  favor of resolution (deadline is inclusive).

## Verdict

No blocking findings. The fail-closed property holds on every path exercised:
every model failure shape, every source failure shape, and every forged-leader
shape tested degrades to INCONCLUSIVE or False, never to a false COMPLIANT/VIOLATION.
