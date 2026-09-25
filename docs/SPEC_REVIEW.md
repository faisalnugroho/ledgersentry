# SPEC REVIEW — LedgerSentry contract vs docs/PLAN.md

Method: line-by-line read of `contracts/ledgersentry.py` against every claim
in `docs/PLAN.md`. No code was modified during this review.

| # | PLAN claim | Contract evidence | Verdict |
|---|---|---|---|
| 1 | Mandatory commit-pinned subject (pinned URL + SHA-256) | `open_audit` requires `PINNED` regex + 64-hex digest; path traversal/query/fragment/userinfo rejected | PASS |
| 2 | 3–8 natural-language requirements, bounded | `3 <= len <= MAX_REQUIREMENTS(8)`, each 10–400 chars, JSON ≤4000 | PASS |
| 3 | Window 60 s–14 days, enforced on-chain | `MIN/MAX_WINDOW_SECONDS`; `open_dispute` sets deadline from `parse_iso_epoch(gl.message_raw["datetime"])`; `resolve` reverts with `response_window_active` before deadline | PASS |
| 4 | ≤4 original evidence while OPEN, ≤3 dispute evidence while DISPUTED | `add_evidence` / `add_dispute_evidence` state-machine guards + `evidence_full` caps | PASS |
| 5 | Dispute evidence rejected when empty per call | `_append_evidence` digest/url validation on every item | PASS |
| 6 | Fair category-split budgets | `budget_plan` equal integer shares per category with per-item caps; module-level `assert` 3000+12000+6000=21000 | PASS |
| 7 | Digest verification on every fetch | `fetch_pinned` compares sha256 to committed digest; mismatch/404/exception → unusable entry | PASS |
| 8 | LLM returns only labels + verbatim citations | `normalize` accepts `labels` (PASS/FAIL/UNCERTAIN ×N), `reason`, `citations[{source,quote}]`; `quote in documents[source]` (ungrounded → fail-safe); verdict field in model output is ignored/overwritten | PASS |
| 9 | PASS must cite subject; subject unfetchable never PASS | hard gate `pass_without_subject_citation`; `pass_without_subject`; subject clamped unusable below 50 chars | PASS |
| 10 | Contract derives verdict (FAIL→VIOLATION, UNCERTAIN→INCONCLUSIVE, else COMPLIANT) | derivation block after labels; COMPLIANT additionally requires zero unusable sources | PASS |
| 11 | Validator re-fetches, compares substance, re-normalizes quotes | `validator`: `equivalent()` on (verdict, labels, manifest), manifest equality, `normalize(proposed) == proposed` against fresh bytes | PASS |
| 12 | Resolve permissionless, terminal immutable | `resolve` has no owner check; resolved audits reject further state changes (`already_resolved`, `audit_not_open`) | PASS |
| 13 | Bounded storage | `TreeMap[str,str]` uniform, ≤100 audits, JSON records with bounded fields | PASS |
| 14 | No money movement, testnet only | no transfer/payable anywhere in the contract | PASS |

## Gaps / notes (honest)

- PLAN says dispute evidence "accepted until resolution" — enforced by design
  (only `resolve` flips status); a post-window append before resolution is
  accepted. This is documented behavior, not a gap.
- The 50-char subject clamp is a deterministic usability gate discovered
  during testing (stub pages must not be PASS-able); PLAN's "bounded, complete
  or fail-closed" covers it.
- No regression found. All 72 direct-mode tests map to these spec rows.


## v1.1 steward remediation addendum (September 2026)

Three Builder-Portal steward findings were addressed with a new revision;
original rows above describe v1.0 and are retained for history.

| # | Steward finding | Remediation | Tests |
|---|---|---|---|
| R1 | No enforceable challenge period before terminal resolution (dispute-only guard) | `open_audit` takes `challenge_seconds` (300–1209600) and writes `challenge_deadline` from the node clock; `resolve` reverts `challenge_period_active` before it for EVERY audit; a dispute still buys a FULL fresh window | test_open_audit_writes_immutable_challenge_deadline, test_resolve_before_challenge_deadline_reverts, test_resolve_after_challenge_deadline_succeeds, test_dispute_restarts_full_window_after_challenge_expiry |
| R2 | Requirement labels not validated against their own citations | citations carry `requirement` index (0-based, range/type checked); every PASS/FAIL needs ≥1 own-requirement citation whose verbatim quote passes a deterministic lexical-overlap gate against that requirement's text (`label_without_related_citation`); UNCERTAIN is exempt; validators re-check the binding | test_label_backed_by_unrelated_requirement_citation_rejected, test_cross_requirement_citation_cannot_support_label, test_each_label_with_own_on_topic_citation_passes, test_citation_requirement_out_of_range_rejected, test_citation_requirement_wrong_type_rejected, test_validator_rejects_forged_citation_requirement |
| R3 | Oversized sources audited only as a prefix | sources longer than their category budget are rejected as INCOMPLETE (`truncated: true`, 0 bytes judged, never decoded into the prompt); any incomplete/missing source forces INCONCLUSIVE | test_oversized_subject_resolved_incomplete_never_prefix_audited, test_oversized_evidence_resolved_incomplete, test_exact_budget_source_audited_in_full |

Direct-mode suite: 94 tests green (was 72); genvm-lint validate.ok.
