"""Real GenVM direct-mode tests; web/LLM boundaries are explicitly mocked."""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
import pytest

OWNER = 'https://raw.githubusercontent.com/example/artifacts/' + 'a' * 40 + '/'
REQS = [
    'The artifact states the total supply of the token and decimals.',
    'The artifact names the deployer account and the deployment date.',
    'The artifact lists all token locks with their release dates.',
]
SUBJECT = ('Token LAUNCH total supply is 1,000,000 with 18 decimals. Deployer is '
           '0xabc deployed on 2026-01-05. Locks: team 40% released 2027-01-05, '
           'community 10% released 2026-07-05.')
EV1 = ('Independent dashboard mirrors the supply of 1,000,000 and 18 decimals '
       'and lists the team lock releasing 2027-01-05.')
EV2 = ('Archive snapshot shows the deployer address 0xabc registered on 2026-01-05.')
FUTURE = '2027-01-01T00:00:00.000000Z'
QUOTE = 'total supply is 1,000,000 with 18 decimals'
SUBJECT_BUDGET = 3000  # mirrors contracts/ledgersentry.py
# Per-requirement subject citations: each label stands on its own on-topic quote.
CITES_FULL = [
    {'source': 0, 'requirement': 0, 'quote': QUOTE},
    {'source': 0, 'requirement': 1, 'quote': 'Deployer is 0xabc deployed on 2026-01-05'},
    {'source': 0, 'requirement': 2, 'quote': 'Locks: team 40% released 2027-01-05'},
]
# A correct quote backing the WRONG requirement (deployer quote offered for req 0).
UNRELATED_CITE = {'source': 0, 'requirement': 0, 'quote': 'Deployer is 0xabc deployed on 2026-01-05'}


def URL(i):
    return OWNER + 'src' + str(i) + '.md'


def sha(body):
    return hashlib.sha256(body.encode() if isinstance(body, str) else body).hexdigest()


def get(c, aid):
    return json.loads(c.get_audit(aid))


def reqs_json(reqs=None):
    return json.dumps(reqs or REQS)


def warp(vm, iso=FUTURE):
    vm.warp(iso)
    sys.modules['genlayer.gl'].message_raw['datetime'] = iso


def epoch(iso):
    return datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S.%f%z').timestamp()


@pytest.fixture
def c(direct_deploy):
    return direct_deploy('contracts/ledgersentry.py')


def open_default(c, aid='audit-1', window=3600, subject=SUBJECT, challenge=3000):
    c.open_audit(aid, 'Token disclosure', URL(0), sha(subject), reqs_json(),
                 window, challenge)
    return aid


def mock_sources(vm, subject=SUBJECT, evidence=(), dispute=(), statuses=None):
    """Register fresh web mocks. Caller registers the LLM mock separately."""
    vm.clear_mocks()
    statuses = statuses or {}
    vm.mock_web(re.escape(URL(0)) + '$', {'status': statuses.get(0, 200), 'body': subject})
    for i, body in enumerate(evidence):
        vm.mock_web(re.escape(URL(i + 1)) + '$', {'status': statuses.get(i + 1, 200), 'body': body})
    base = 1 + len(evidence)
    for i, body in enumerate(dispute):
        vm.mock_web(re.escape(URL(base + i)) + '$', {'status': 200, 'body': body})


def model(req_count, labels=None, reason='The subject demonstrates each requirement in order.',
          citations=None):
    labels = labels or ['PASS'] * req_count
    if citations is None:
        citations = CITES_FULL if req_count == 3 else []
    return {'labels': labels, 'reason': reason, 'citations': citations}


def resolve(c, vm, aid='audit-1', subject=SUBJECT, evidence=(), dispute=(),
            output=None, statuses=None):
    mock_sources(vm, subject, evidence, dispute, statuses)
    vm.mock_llm('.*', json.dumps(output if output is not None else model(3)))
    c.resolve(aid)
    return get(c, aid)


# ---------- open_audit input validation ----------

@pytest.mark.parametrize('field,value,reason', [
    ('aid', '', 'invalid_audit_id'), ('aid', '../escape', 'invalid_audit_id'),
    ('aid', 'XyZ', 'invalid_audit_id'), ('aid', 'a' * 41, 'invalid_audit_id'),
    ('title', '  ', 'invalid_title'), ('title', 'a' * 121, 'invalid_title'),
    ('window', 0, 'invalid_window'), ('window', -5, 'invalid_window'),
    ('window', 59, 'invalid_window'), ('window', 1209601, 'invalid_window'),
    ('challenge', 0, 'invalid_challenge'), ('challenge', -1, 'invalid_challenge'),
    ('challenge', 299, 'invalid_challenge'), ('challenge', 1209601, 'invalid_challenge'),
    ('challenge', True, 'invalid_challenge'), ('challenge', '600', 'invalid_challenge'),
    ('digest', 'abc', 'invalid_digest'), ('digest', 'A' * 64, 'invalid_digest'),
    ('digest', 'g' * 64, 'invalid_digest'), ('digest', 'a' * 63, 'invalid_digest'),
])
def test_open_audit_validation(c, direct_vm, field, value, reason):
    args = {'aid': 'audit-x', 'title': 'Token disclosure', 'uri': URL(0),
            'digest': sha(SUBJECT), 'reqs': reqs_json(), 'window': 3600,
            'challenge': 3600}
    args[field] = value
    with direct_vm.expect_revert(reason):
        c.open_audit(args['aid'], args['title'], args['uri'], args['digest'],
                     args['reqs'], args['window'], args['challenge'])


@pytest.mark.parametrize('reqs,reason', [
    ([], 'invalid_requirements'),
    (['x' * 9, 'y' * 9, 'z' * 9], 'invalid_requirement'),
    (REQS + ['x' * 15] * 6, 'invalid_requirements'),
    ('not-a-list', 'invalid_requirements'),
    (123, 'invalid_requirements'),
])
def test_requirements_validation(c, direct_vm, reqs, reason):
    with direct_vm.expect_revert(reason):
        c.open_audit('audit-x', 'Title here', URL(0), sha(SUBJECT),
                     json.dumps(reqs) if not isinstance(reqs, list) else json.dumps(reqs),
                     3600, 3600)


@pytest.mark.parametrize('uri', [
    'http://localhost/x.md', 'https://127.0.0.1/x.md',
    'https://raw.githubusercontent.com.evil.test/a/b/' + 'a' * 40 + '/x.md',
    'https://raw.githubusercontent.com/a/b/main/x.md',
    OWNER + '../secret.md', OWNER + './x.md', OWNER + 'x.md?query=1',
    OWNER + 'x.md#frag', OWNER + 'x.json', OWNER + 'a//x.md',
    'https://user@raw.githubusercontent.com/a/b/' + 'a' * 40 + '/x.md',
])
def test_url_allowlist(c, direct_vm, uri):
    with direct_vm.expect_revert('invalid_'):
        c.open_audit('audit-x', 'Title here', uri, sha(SUBJECT), reqs_json(), 3600, 3600)


def test_open_duplicate_and_unknown(c, direct_vm):
    open_default(c)
    with direct_vm.expect_revert('audit_exists'):
        open_default(c)
    with direct_vm.expect_revert('audit_not_found'):
        c.get_audit('missing')


def test_registry_capacity(c, direct_vm):
    for i in range(100):
        c.open_audit('r-' + str(i), 'Title ' + str(i), URL(0), sha(SUBJECT),
                     reqs_json(), 3600, 300)
    with direct_vm.expect_revert('registry_full'):
        c.open_audit('r-100', 'Title 100', URL(0), sha(SUBJECT), reqs_json(), 3600, 300)


# ---------- evidence lifecycle ----------

def test_add_evidence_lifecycle(c, direct_vm):
    open_default(c)
    c.add_evidence('audit-1', URL(1), sha(EV1))
    c.add_evidence('audit-1', URL(2), sha(EV2))
    record = get(c, 'audit-1')
    assert [e['url'] for e in record['evidence']] == [URL(1), URL(2)]
    with direct_vm.expect_revert('duplicate_digest'):
        c.add_evidence('audit-1', URL(3), sha(EV1))
    with direct_vm.expect_revert('invalid_pinned_url'):
        c.add_evidence('audit-1', 'https://evil.test/x.md', sha('x' * 25))
    with direct_vm.expect_revert('invalid_digest'):
        c.add_evidence('audit-1', URL(3), 'nope')


def test_evidence_capacity(c, direct_vm):
    open_default(c)
    for i in range(4):
        c.add_evidence('audit-1', URL(i + 1), sha(EV1 + str(i)))
    with direct_vm.expect_revert('evidence_full'):
        c.add_evidence('audit-1', URL(9), sha(EV1 + 'new'))


def test_dispute_evidence_capacity(c, direct_vm):
    open_default(c)
    c.open_dispute('audit-1')
    for i in range(3):
        c.add_dispute_evidence('audit-1', URL(i + 1), sha(EV1 + str(i)))
    with direct_vm.expect_revert('evidence_full'):
        c.add_dispute_evidence('audit-1', URL(9), sha(EV1 + 'new'))


def test_state_machine_categories(c, direct_vm):
    open_default(c)
    with direct_vm.expect_revert('audit_not_disputed'):
        c.add_dispute_evidence('audit-1', URL(5), sha(EV1))
    c.open_dispute('audit-1')
    with direct_vm.expect_revert('audit_not_open'):
        c.add_evidence('audit-1', URL(1), sha(EV1))
    c.add_dispute_evidence('audit-1', URL(4), sha(EV1))
    record = get(c, 'audit-1')
    assert record['status'] == 'DISPUTED'
    assert record['dispute'][0]['url'] == URL(4)


# ---------- challenge period (universal, pre-deadline resolution) ----------

def test_open_audit_writes_immutable_challenge_deadline(c, direct_vm):
    warp(direct_vm)  # pin the node clock so the deadline math is exact
    open_default(c, challenge=3600)
    record = get(c, 'audit-1')
    assert record['challenge_seconds'] == 3600
    assert record['challenge_deadline'] > 1700000000
    # Deterministic honest-clock math: now + 3600 (+/-1s of drift).
    assert abs(record['challenge_deadline'] - (epoch(FUTURE) + 3600)) <= 1


def test_resolve_before_challenge_deadline_reverts(c, direct_vm):
    open_default(c, challenge=3600)
    mock_sources(direct_vm)
    direct_vm.mock_llm('.*', json.dumps(model(3)))
    with direct_vm.expect_revert('challenge_period_active'):
        c.resolve('audit-1')
    record = get(c, 'audit-1')
    assert record['status'] == 'OPEN'
    assert record['result'] == {}


def test_resolve_after_challenge_deadline_succeeds(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm)
    assert record['status'] == 'RESOLVED'
    assert record['result']['verdict'] == 'COMPLIANT'


def test_dispute_restarts_full_window_after_challenge_expiry(c, direct_vm):
    open_default(c, window=3600, challenge=300)
    warp(direct_vm)  # challenge period has fully expired
    c.open_dispute('audit-1')
    record = get(c, 'audit-1')
    assert record['status'] == 'DISPUTED'
    # A dispute AFTER challenge expiry still buys a FULL fresh window.
    assert abs(record['dispute_deadline'] - (epoch(FUTURE) + 3600)) <= 1
    with direct_vm.expect_revert('response_window_active'):
        c.resolve('audit-1')


# ---------- dispute window ----------

def test_open_dispute_sets_deadline(c, direct_vm):
    open_default(c, window=3600)
    c.open_dispute('audit-1')
    record = get(c, 'audit-1')
    assert record['status'] == 'DISPUTED'
    assert record['dispute_deadline'] > 1700000000


def test_resolve_blocked_during_window(c, direct_vm):
    open_default(c, window=3600, challenge=300)
    warp(direct_vm)  # challenge period over; only the dispute window blocks
    mock_sources(direct_vm)
    direct_vm.mock_llm('.*', json.dumps(model(3)))
    c.open_dispute('audit-1')
    with direct_vm.expect_revert('response_window_active'):
        c.resolve('audit-1')
    record = get(c, 'audit-1')
    assert record['status'] == 'DISPUTED'
    assert record['result'] == {}


def test_resolve_while_challenge_active_and_disputed_reverts(c, direct_vm):
    open_default(c, window=60, challenge=7200)
    c.open_dispute('audit-1')
    mock_sources(direct_vm)
    direct_vm.mock_llm('.*', json.dumps(model(3)))
    with direct_vm.expect_revert('challenge_period_active'):
        c.resolve('audit-1')


def test_resolve_allowed_after_window(c, direct_vm):
    open_default(c, window=60, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm)
    assert record['status'] == 'RESOLVED'
    assert record['result']['verdict'] == 'COMPLIANT'


def test_double_dispute_and_resolution_terminality(c, direct_vm):
    open_default(c)
    c.open_dispute('audit-1')
    with direct_vm.expect_revert('audit_not_open'):
        c.open_dispute('audit-1')
    warp(direct_vm)
    resolve(c, direct_vm, output=model(3, citations=CITES_FULL))
    with direct_vm.expect_revert('already_resolved'):
        c.resolve('audit-1')
    with direct_vm.expect_revert('audit_not_open'):
        c.open_dispute('audit-1')


# ---------- resolve decision matrix ----------

def test_compliant_happy_path(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    c.add_evidence('audit-1', URL(1), sha(EV1))
    record = resolve(c, direct_vm, evidence=[EV1],
                     output=model(3, citations=CITES_FULL))
    assert record['status'] == 'RESOLVED'
    assert record['result']['verdict'] == 'COMPLIANT'
    assert record['result']['labels'] == ['PASS', 'PASS', 'PASS']
    assert record['result']['manifest'][0]['digest_ok'] is True
    assert record['result']['manifest'][1]['digest_ok'] is True


@pytest.mark.parametrize('labels,verdict', [
    (['FAIL', 'PASS', 'PASS'], 'VIOLATION'),
    (['PASS', 'FAIL', 'FAIL'], 'VIOLATION'),
    (['UNCERTAIN', 'PASS', 'PASS'], 'INCONCLUSIVE'),
    (['PASS', 'PASS', 'UNCERTAIN'], 'INCONCLUSIVE'),
    (['FAIL', 'UNCERTAIN', 'PASS'], 'VIOLATION'),
])
def test_contract_derives_verdict(c, direct_vm, labels, verdict):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, labels, citations=CITES_FULL))
    assert record['result']['verdict'] == verdict
    assert record['result']['labels'] == labels


# ---------- fail-closed evidence gates ----------

def test_pass_without_subject_citation_rejected(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=[]))
    assert record['result']['verdict'] == 'INCONCLUSIVE'


def test_dead_subject_never_passes(c, direct_vm):
    thin = 'This placeholder page intentionally left empty.'
    open_default(c, subject=thin, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, subject=thin, output=model(3, citations=[
        {'source': 0, 'requirement': 0,
         'quote': 'placeholder page intentionally left empty.'}]))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    assert record['result']['manifest'][0]['digest_ok'] is False


def test_subject_fetch_failure_fails_closed(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, statuses={0: 404}, output=model(3))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    assert record['result']['manifest'][0]['digest_ok'] is False


def test_tampered_subject_detected(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, subject=SUBJECT + ' tampered', output=model(3))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    assert record['result']['manifest'][0]['digest_ok'] is False


def test_unfetched_dispute_cannot_force_pass(c, direct_vm):
    open_default(c)
    mock_sources(direct_vm)
    direct_vm.mock_llm('.*', json.dumps(model(3)))
    c.open_dispute('audit-1')
    c.add_dispute_evidence('audit-1', URL(4), sha(EV1))
    warp(direct_vm)
    record = resolve(c, direct_vm, dispute=[])
    assert record['result']['verdict'] == 'INCONCLUSIVE'


# ---------- steward finding: oversized sources resolved incomplete ----------

def test_oversized_subject_resolved_incomplete_never_prefix_audited(c, direct_vm):
    bloated = ('Token LAUNCH total supply is 1,000,000 with 18 decimals. ' +
               'Filler padding sentence. ' * 400)
    assert len(bloated.encode()) > SUBJECT_BUDGET
    open_default(c, subject=bloated, challenge=300)
    warp(direct_vm)
    # The model claims PASS with in-prefix quotes — the source is still
    # unauditable: resolved as incomplete, never judged from a prefix.
    record = resolve(c, direct_vm, subject=bloated, output=model(3, citations=[
        {'source': 0, 'requirement': 0, 'quote': QUOTE},
        {'source': 0, 'requirement': 1,
         'quote': 'Deployer is 0xabc deployed on 2026-01-05'},
        {'source': 0, 'requirement': 2,
         'quote': 'Locks: team 40% released 2027-01-05'}]))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    entry = record['result']['manifest'][0]
    assert entry['digest_ok'] is True and entry['truncated'] is True
    assert entry['bytes'] == 0
    assert record['result']['citations'] == []


def test_oversized_evidence_resolved_incomplete(c, direct_vm):
    bloated = EV1 + ' Extra padding text. ' * 2000
    open_default(c, challenge=300)
    warp(direct_vm)
    c.add_evidence('audit-1', URL(1), sha(bloated))
    record = resolve(c, direct_vm, evidence=[bloated], output=model(3))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    entry = record['result']['manifest'][1]
    assert entry['digest_ok'] is True and entry['truncated'] is True
    assert entry['bytes'] == 0


def test_exact_budget_source_audited_in_full(c, direct_vm):
    # Normal sources are fetched whole and never marked truncated.
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm)
    entry = record['result']['manifest'][0]
    assert entry['digest_ok'] is True and entry['truncated'] is False
    assert entry['bytes'] == len(SUBJECT)
    assert record['result']['verdict'] == 'COMPLIANT'


def test_contradictory_text_beyond_analysis_limit_fails_closed(c, direct_vm):
    # STEWARD: contradictory text beyond the analysis limit. The subject's
    # first SUBJECT_BUDGET bytes read fully compliant; the contradiction
    # deliberately sits AFTER the budget, so only a prefix-audit (or any
    # truncated use of the source) could ever score the subject COMPLIANT.
    head = ('Token LAUNCH total supply is 1,000,000 with 18 decimals. Deployer is '
            '0xabc deployed on 2026-01-05. Locks: team 40% released 2027-01-05, '
            'community 10% released 2026-07-05. ')
    tail = ('CONTRADICTION: the team lock was revoked and the supply was secretly '
            'minted to 2,000,000; earlier statements are no longer accurate. ' * 100)
    bloated = head + tail
    assert len(head.encode()) < SUBJECT_BUDGET < len(bloated.encode())
    open_default(c, subject=bloated, challenge=300)
    warp(direct_vm)
    # The model claims every requirement PASS using in-head (in-prefix) quotes.
    output = model(3, citations=[
        {'source': 0, 'requirement': 0, 'quote': QUOTE},
        {'source': 0, 'requirement': 1,
         'quote': 'Deployer is 0xabc deployed on 2026-01-05'},
        {'source': 0, 'requirement': 2,
         'quote': 'Locks: team 40% released 2027-01-05'}])
    mock_sources(direct_vm, subject=bloated)
    direct_vm.mock_llm('.*', json.dumps(output))
    seen = []
    original = direct_vm._match_llm_mock

    def spy(prompt):
        seen.append(prompt)
        return original(prompt)

    direct_vm._match_llm_mock = spy
    c.resolve('audit-1')
    direct_vm._match_llm_mock = original
    record = get(c, 'audit-1')
    # 1. No prefix of the source reaches the model: neither the compliant
    #    head (a prefix-audit would have passed) nor the beyond-limit
    #    contradiction is present in the prompt — the oversized source is
    #    dropped whole, never audited as a prefix.
    assert len(seen) >= 1
    assert QUOTE not in seen[0]
    assert 'CONTRADICTION' not in seen[0]
    # 2. Digest-verified but recorded as truncated / incomplete, zero bytes.
    entry = record['result']['manifest'][0]
    assert entry['digest_ok'] is True and entry['truncated'] is True
    assert entry['bytes'] == 0
    # 3. The contradictory source contributes no usable citation.
    assert record['result']['citations'] == []
    # 4+5. Labels cannot stand (no auditable subject text), so the verdict
    #    can never become COMPLIANT from this source: fail-closed.
    assert record['result']['labels'] == ['UNCERTAIN', 'UNCERTAIN', 'UNCERTAIN']
    assert record['result']['verdict'] == 'INCONCLUSIVE'


# ---------- steward finding: per-requirement citation enforcement ----------

def test_label_backed_by_unrelated_requirement_citation_rejected(c, direct_vm):
    # The model MIS-TAGS a stray deployer quote as req 0's citation. The
    # contract re-associates every quote by content: the stray quote is
    # inferred to req 1 (its only lexical topic), req 0 keeps its own supply
    # quote, and every label still stands on its own on-topic citation ->
    # honest COMPLIANT outcome survives the model's tag confusion.
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=[
        {'source': 0, 'requirement': 0,
         'quote': 'Deployer is 0xabc deployed on 2026-01-05'},
        CITES_FULL[0], CITES_FULL[1], CITES_FULL[2]]))
    assert record['result']['verdict'] == 'COMPLIANT'
    reqs = sorted(c['requirement'] for c in record['result']['citations'])
    assert reqs == [0, 1, 2]


def test_unfixable_label_without_any_related_citation_degrades(c, direct_vm):
    # Req 2's label has NO on-topic citation anywhere (locks are never
    # quoted): the contract cannot repair it, so the label degrades to
    # UNCERTAIN and the verdict is INCONCLUSIVE — per-label fail-closed.
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=[
        CITES_FULL[0], CITES_FULL[1]]))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    assert record['result']['labels'] == ['PASS', 'PASS', 'UNCERTAIN']


def test_cross_requirement_citation_cannot_support_label(c, direct_vm):
    # The supply quote is tagged as requirement 2's citation (locks): the
    # contract re-associates it by content to req 0, so it can NEVER carry
    # req 2's label — req 2 keeps its own on-topic lock quote and the honest
    # outcome survives the model's tag confusion.
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=[
        {'source': 0, 'requirement': 2, 'quote': QUOTE},
        CITES_FULL[1], CITES_FULL[2]]))
    assert record['result']['verdict'] == 'COMPLIANT'
    supply_cites = [c for c in record['result']['citations'] if c['quote'] == QUOTE]
    assert supply_cites and supply_cites[0]['requirement'] == 0


def test_each_label_with_own_on_topic_citation_passes(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3))
    assert record['result']['verdict'] == 'COMPLIANT'
    assert record['result']['citations'] == CITES_FULL


def test_fail_label_also_needs_related_citation(c, direct_vm):
    # The FAIL label's only possible support is a deployer quote, which the
    # contract re-assigns to req 1: req 0's FAIL stands unproven and degrades
    # to UNCERTAIN. A FAIL can never be manufactured from an off-topic quote.
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(
        3, ['FAIL', 'PASS', 'PASS'], citations=[
            {'source': 0, 'requirement': 0,
             'quote': 'Deployer is 0xabc deployed on 2026-01-05'},
            CITES_FULL[1], CITES_FULL[2]]))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    assert record['result']['labels'] == ['UNCERTAIN', 'PASS', 'PASS']


def test_uncertain_label_needs_no_citation(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(
        3, ['PASS', 'PASS', 'UNCERTAIN'], citations=CITES_FULL[:2]))
    assert record['result']['verdict'] == 'INCONCLUSIVE'  # UNCERTAIN present
    assert len(record['result']['citations']) == 2


def test_citation_requirement_out_of_range_ignored(c, direct_vm):
    # Model tags carry no authority: the contract re-derives requirements
    # from content, so a bogus out-of-range tag is simply ignored and the
    # honest outcome stands.
    open_default(c, challenge=300)
    warp(direct_vm)
    bad = [dict(cite, requirement=3) for cite in CITES_FULL]
    record = resolve(c, direct_vm, output=model(3, citations=bad))
    assert record['result']['verdict'] == 'COMPLIANT'


def test_citation_requirement_wrong_type_ignored(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    bad = [dict(CITES_FULL[0], requirement='0')] + CITES_FULL[1:]
    record = resolve(c, direct_vm, output=model(3, citations=bad))
    assert record['result']['verdict'] == 'COMPLIANT'


def test_validator_rejects_forged_citation_requirement(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3))
    forged = json.loads(json.dumps(record['result']))
    forged['citations'][0]['requirement'] = 1
    outcome = direct_vm.run_validator(leader_result=forged)
    assert outcome is False


def test_validator_rejects_forged_quote(c, direct_vm):
    # A tampered quote fails the verbatim substring check in the validator's
    # independent re-normalization.
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3))
    forged = json.loads(json.dumps(record['result']))
    forged['citations'][0]['quote'] = 'total supply is 1,000,000 with 18 decimalss'
    outcome = direct_vm.run_validator(leader_result=forged)
    assert outcome is False


# ---------- model shape / grounding ----------

@pytest.mark.parametrize('output,expect_verdict', [
    (model(2), 'INCONCLUSIVE'),
    (model(3, ['pass', 'PASS', 'PASS']), 'INCONCLUSIVE'),
    ({'labels': ['PASS'] * 3}, 'INCONCLUSIVE'),
    (model(3, reason='short'), 'COMPLIANT'),  # thin reason recovered deterministically
    ({'labels': ['PASS'] * 3, 'reason': 'r' * 30, 'citations': 'no'}, 'INCONCLUSIVE'),
    (model(3, citations=[{'source': 0, 'requirement': 0, 'quote': 'too short'}]),
     'INCONCLUSIVE'),
    (model(3, citations=[{'source': 9, 'requirement': 0, 'quote': 'x' * 40}]),
     'INCONCLUSIVE'),
    (model(3, citations=CITES_FULL + [
        {'quote': 'garbage citation entry without required keys'},
        {'source': 'zero', 'requirement': 1, 'quote': QUOTE}]),
     'COMPLIANT'),  # malformed entries dropped, valid ones survive
    ('not-json-at-all', 'INCONCLUSIVE'),
])
def test_model_shape_fail_safe(c, direct_vm, output, expect_verdict):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=output)
    assert record['result']['verdict'] == expect_verdict


def test_lowercase_label_vocabulary_degrades_to_uncertain(c, direct_vm):
    # Unknown model vocabulary ('pass') is not a proven label: it degrades to
    # UNCERTAIN instead of nuking the audit — but the verdict stays honest.
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, ['pass', 'PASS', 'PASS']))
    assert record['result']['verdict'] == 'INCONCLUSIVE'
    assert record['result']['labels'][0] == 'UNCERTAIN'


def test_grounded_citation_kept(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3))
    assert record['result']['verdict'] == 'COMPLIANT'
    assert record['result']['citations'][0]['source'] == 0
    assert record['result']['citations'][0]['quote'] == QUOTE


def test_ungrounded_quote_rejected(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=[
        {'source': 0, 'requirement': 0,
         'quote': 'this exact sentence never appears in subject'}]))
    assert record['result']['verdict'] == 'INCONCLUSIVE'


def test_llm_cannot_pick_verdict_field(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    output = {'verdict': 'COMPLIANT', 'labels': ['FAIL', 'FAIL', 'FAIL'],
              'reason': 'The model tries to smuggle a verdict field through.',
              'citations': CITES_FULL}
    record = resolve(c, direct_vm, output=output)
    assert record['result']['verdict'] == 'VIOLATION'


# ---------- consensus equivalence: forged / divergent leaders ----------

def test_validator_accepts_honest_leader(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    c.add_evidence('audit-1', URL(1), sha(EV1))
    record = resolve(c, direct_vm, evidence=[EV1], output=model(3, citations=CITES_FULL))
    outcome = direct_vm.run_validator(leader_result=record['result'])
    assert outcome is True


def test_forged_leader_label_rejected(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    c.add_evidence('audit-1', URL(1), sha(EV1))
    record = resolve(c, direct_vm, evidence=[EV1], output=model(3, citations=CITES_FULL))
    forged = json.loads(json.dumps(record['result']))
    forged['labels'] = ['PASS', 'FAIL', 'PASS']
    outcome = direct_vm.run_validator(leader_result=forged)
    assert outcome is False


def test_forged_leader_verdict_rejected(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=CITES_FULL))
    forged = json.loads(json.dumps(record['result']))
    forged['verdict'] = 'VIOLATION'
    outcome = direct_vm.run_validator(leader_result=forged)
    assert outcome is False


def test_forged_manifest_rejected(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=CITES_FULL))
    forged = json.loads(json.dumps(record['result']))
    forged['manifest'][0]['digest_ok'] = False
    outcome = direct_vm.run_validator(leader_result=forged)
    assert outcome is False


def test_divergent_fetch_rejected(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=CITES_FULL))
    honest = json.loads(json.dumps(record['result']))
    direct_vm.clear_mocks()
    direct_vm.mock_web(re.escape(URL(0)) + '$', {'status': 200, 'body': SUBJECT + ' mutated'})
    direct_vm.mock_llm('.*', json.dumps(model(3, citations=CITES_FULL)))
    outcome = direct_vm.run_validator(leader_result=honest)
    assert outcome is False


# ---------- budget fairness (prompt-spy) ----------

def test_budget_order_in_prompt(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    for i in range(4):
        c.add_evidence('audit-1', URL(i + 1), sha(EV1 + str(i)))
    c.open_dispute('audit-1')
    c.add_dispute_evidence('audit-1', URL(5), sha(EV2))
    warp(direct_vm, iso='2027-01-01T02:00:00.000000Z')  # past window end
    mock_sources(direct_vm, evidence=[EV1 + str(i) for i in range(4)], dispute=[EV2])
    direct_vm.mock_llm('.*', json.dumps(model(3, citations=CITES_FULL)))
    seen = []
    original = direct_vm._match_llm_mock

    def spy(prompt):
        seen.append(prompt)
        return original(prompt)

    direct_vm._match_llm_mock = spy
    c.resolve('audit-1')
    direct_vm._match_llm_mock = original
    assert len(seen) >= 1
    prompt = seen[0]
    # The prompt embeds fetched BODIES (not URLs) in frozen deterministic
    # order: subject first, then original evidence, then dispute evidence.
    assert prompt.index(SUBJECT) < prompt.index(EV1 + '0') < prompt.index(EV1 + '1') \
        < prompt.index(EV1 + '2') < prompt.index(EV1 + '3') < prompt.index(EV2)


def test_budget_invariant_holds(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    for i in range(4):
        c.add_evidence('audit-1', URL(i + 1), sha(EV1 + str(i)))
    record = resolve(c, direct_vm, evidence=[EV1 + str(i) for i in range(4)],
                     output=model(3, citations=CITES_FULL))
    manifest = record['result']['manifest']
    assert len(manifest) == 5
    assert all(item['digest_ok'] for item in manifest)
    # 3000 subject + 4 x 3000 original shares, all fetched fully
    assert manifest[0]['bytes'] == len(SUBJECT)


def test_manifest_counts_fetched_bytes(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    record = resolve(c, direct_vm, output=model(3, citations=CITES_FULL))
    manifest = record['result']['manifest']
    assert manifest[0]['bytes'] == len(SUBJECT)
    assert manifest[0]['digest_ok'] is True


# ---------- immutability + listing ----------

def test_record_immutability_after_resolution(c, direct_vm):
    open_default(c, challenge=300)
    warp(direct_vm)
    before = get(c, 'audit-1')
    resolve(c, direct_vm, output=model(3, citations=CITES_FULL))
    after = get(c, 'audit-1')
    assert before['evidence'] == after['evidence']
    assert before['subject'] == after['subject']
    assert after['status'] == 'RESOLVED'


def test_list_roundtrips(c, direct_vm):
    assert json.loads(c.list_audits()) == []
    open_default(c, aid='first')
    open_default(c, aid='second')
    assert json.loads(c.list_audits()) == ['first', 'second']
