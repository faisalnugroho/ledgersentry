"""Real Studionet deployment and live smoke for LedgerSentry. Never submits Portal.
Usage: python scripts/live_smoke.py --deploy; python scripts/live_smoke.py --smoke
Resumes logged transaction hashes, never silently re-sends an uncertain write.
"""
import argparse
import base64
import hashlib
import json
import time
from pathlib import Path
from urllib.request import urlopen
import requests
from genlayer_py import create_client, create_account
from genlayer_py.chains import studionet

import threading

def call_with_timeout(fn, seconds, *args, **kwargs):
    """SDK calls have no timeout parameter; a silent Cloudflare hold can hang
    a socket open forever. Hard-timeout every SDK call from a helper thread."""
    box = {}
    def target():
        try:
            box["result"] = fn(*args, **kwargs)
        except BaseException as err:
            box["error"] = err
    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(seconds)
    if t.is_alive():
        raise TimeoutError("sdk call exceeded " + str(seconds) + "s")
    if "error" in box:
        raise box["error"]
    return box["result"]

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "evidence/live.json"
KEY = Path.home() / ".genlayer-keys/ledgersentry-key.json"
RPC = "https://studio.genlayer.com/api"
REV = "2ecf05c13e6cfe6318ba61a91ef033927c24dc09"  # deployed commit pinning every example source (full 40-hex: contract regex requires it)
BASE = "https://raw.githubusercontent.com/faisalnugroho/ledgersentry"
CHALLENGE = 86400  # universal challenge period written at open_audit

REQS = [
    "The artifact states the total supply of the token and its decimals.",
    "The artifact names the deployer account and the deployment date.",
    "The artifact states its token-lock list is complete (no other token locks exist) and lists each lock with its release date.",
]
SUBJECT_OK = 'Token LAUNCH total supply is 1,000,000 with 18 decimals. Deployer is 0xabc deployed on 2026-01-05. Locks: team 40% released 2027-01-05, community 10% released 2026-07-05. This lock list is complete; no other token locks exist for LAUNCH.\n'
SUBJECT_BAD = 'Token LAUNCH total supply is 1,000,000 with 18 decimals. Deployer is 0xabc deployed on 2026-01-05. The team lock of 40% was quietly removed from this statement; no locks are disclosed at all in this version.\n'
SUBJECT_THIN = 'Tiny stub page.\n'
EV_DASH = 'Independent dashboard mirrors the supply of 1,000,000 and 18 decimals and lists the team lock releasing 2027-01-05.\n'
EV_ARCHIVE = 'Archive snapshot shows the deployer address 0xabc registered on 2026-01-05.\n'
EV_REBUTTAL = 'Dispute rebuttal: the audit subject remains accurate. The independent dashboard mirrors the supply of 1,000,000 and 18 decimals and lists the team lock releasing 2027-01-05.\n'


def rpc(method, params):
    last = None
    for attempt in range(5):
        try:
            response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=45)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError(data["error"])
            return data["result"]
        except (requests.exceptions.RequestException, RuntimeError) as err:
            last = err
            if attempt == 4:
                raise
            print("rpc error, retrying:", str(err)[:120], flush=True)
            time.sleep(10 * (attempt + 1))
    raise last


def save(data):
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text(json.dumps(data, indent=2))


def wait(tx):
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        record = rpc("eth_getTransactionByHash", [tx])
        if record and record.get("status") in ("FINALIZED", "UNDETERMINED", "CANCELED"):
            return record
        time.sleep(10)
    raise TimeoutError("Transaction pending; resume by hash, do not resubmit: " + tx)


def succeeded(record):
    leaders = (record.get("consensus_data") or {}).get("leader_receipt") or []
    execution = record.get("tx_execution_result_name") or (leaders[0].get("execution_result") if leaders else None)
    return record.get("status") == "FINALIZED" and record.get("result_name") == "MAJORITY_AGREE" and execution in ("FINISHED_WITH_RETURN", "SUCCESS")


def pinned(name):
    assert REV, "set REV to the deployed commit hash before smoking"
    return f"{BASE}/{REV}/examples/{name}"


def sha(body):
    return hashlib.sha256(body.encode() if isinstance(body, str) else body).hexdigest()


def fetch_bytes(url):
    with urlopen(url, timeout=30) as res:
        return res.read()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if not args.deploy and not args.smoke:
        parser.error("choose --deploy or --smoke")
    KEY.parent.mkdir(exist_ok=True)
    if KEY.exists():
        account = create_account(account_private_key=json.loads(KEY.read_text())["private_key"])
    else:
        account = create_account()
        KEY.touch(mode=0o600)
        KEY.write_text(json.dumps({"address": account.address, "private_key": account.key.hex()}))
    client = create_client(chain=studionet, account=account)
    log = json.loads(LOG.read_text()) if LOG.exists() else {"network": "studionet", "rpc": RPC, "owner": account.address, "steps": {}}
    if args.deploy:
        source = (ROOT / "contracts/ledgersentry.py").read_text()
        if "deploy_tx" not in log:
            client.fund_account(account.address, 10**18)
            log["source_sha256"] = hashlib.sha256(source.encode()).hexdigest()
            log["deploy_tx"] = client.deploy_contract(code=source, account=client.local_account, args=[], leader_only=False)
            save(log)
            print("deploy", log["deploy_tx"], flush=True)
        receipt = wait(log["deploy_tx"])
        log["deploy_receipt"] = receipt
        save(log)
        if not succeeded(receipt):
            raise RuntimeError("Deployment execution/consensus not successful: " + json.dumps(receipt))
        address = (receipt.get("data") or {}).get("contract_address") or receipt.get("to_address")
        assert address, "no deployment address"
        log["address"] = address
        actual_code = base64.b64decode(receipt["data"]["contract_code"])
        assert hashlib.sha256(actual_code).hexdigest() == log["source_sha256"]
        assert json.loads(client.read_contract(address=address, function_name="list_audits", args=[])) == [] or log["steps"]
        save(log)
        (ROOT / "frontend").mkdir(exist_ok=True)
        (ROOT / "frontend/deployment.json").write_text(json.dumps({"address": address, "network": "studionet", "chainId": 61999, "deployTx": log["deploy_tx"]}, indent=2))
        print("DEPLOY_VERIFIED", address, flush=True)
    if not args.smoke:
        return
    address = log["address"]

    def write(label, method, values, expected_success=True):
        step = log["steps"].get(label)
        if not step:
            tx = None
            for attempt in range(4):
                try:
                    tx = call_with_timeout(client.write_contract, 120, address=address, function_name=method, args=values, account=client.local_account, leader_only=False)
                    break
                except Exception as err:
                    if attempt == 3:
                        raise
                    print("rpc error, retrying:", str(err)[:120], flush=True)
                    time.sleep(20 * (attempt + 1))
            step = {"tx": tx, "method": method, "args": values}
            log["steps"][label] = step
            save(log)
            print(label, tx, flush=True)
        receipt = wait(step["tx"])
        step["receipt"] = receipt
        step["success"] = succeeded(receipt)
        save(log)
        if step["success"] != expected_success:
            raise RuntimeError("Unexpected transaction outcome at " + label + ": " + json.dumps(receipt))
        print(label, "verified", receipt.get("result_name"), receipt.get("tx_execution_result_name"), flush=True)

    def read(aid):
        last = None
        for attempt in range(5):
            try:
                return json.loads(call_with_timeout(client.read_contract, 90, address=address, function_name="get_audit", args=[aid]))
            except Exception as err:
                last = err
                if attempt == 4:
                    raise
                print("read error, retrying:", str(err)[:120], flush=True)
                time.sleep(10 * (attempt + 1))
        raise last

    def audit(label, aid, subject_file, subject_body, evidence=(), window=3600,
              challenge=CHALLENGE):
        write(label + "-open", "open_audit", [aid, "Live smoke: " + aid, pinned(subject_file), sha(subject_body), json.dumps(REQS), window, challenge])
        for i, (name, body) in enumerate(evidence):
            write(f"{label}-ev{i}", "add_evidence", [aid, pinned(name), sha(body)])

    def wait_until(ts, why):
        pause = ts - time.time() + 10
        if pause > 0:
            print("waiting %ds until %s..." % (int(pause), why), flush=True)
            time.sleep(pause)

    def deadline_of(aid, key):
        return read(aid).get(key) or 0

    # 1-2: compliance-positive audit with mirrored evidence -> COMPLIANT
    # (challenge=300: the smoke waits out the challenge period, then resolves
    # — universal pre-deadline revert is exercised by the direct tests.)
    audit("clean", "ls-clean", "subject-ok.md", SUBJECT_OK,
          evidence=[("evidence-dashboard.md", EV_DASH), ("evidence-archive.md", EV_ARCHIVE)],
          challenge=300)
    wait_until(deadline_of("ls-clean", "challenge_deadline"), "ls-clean challenge end")
    write("clean-resolve", "resolve", ["ls-clean"])
    record = read("ls-clean")
    log.setdefault("audits", {})["ls-clean"] = record
    save(log)
    assert record["status"] == "RESOLVED" and record["result"]["verdict"] == "COMPLIANT", record

    # 3: violating subject (locks removed) -> VIOLATION
    audit("violation", "ls-violation", "subject-bad.md", SUBJECT_BAD, challenge=300)
    wait_until(deadline_of("ls-violation", "challenge_deadline"), "ls-violation challenge end")
    write("violation-resolve", "resolve", ["ls-violation"])
    record = read("ls-violation")
    log.setdefault("audits", {})["ls-violation"] = record
    save(log)
    assert record["status"] == "RESOLVED" and record["result"]["verdict"] == "VIOLATION", record

    # 4: thin (49-char) subject -> deterministic fail-closed INCONCLUSIVE
    audit("inconclusive", "ls-thin", "subject-thin.md", SUBJECT_THIN, challenge=300)
    wait_until(deadline_of("ls-thin", "challenge_deadline"), "ls-thin challenge end")
    write("inconclusive-resolve", "resolve", ["ls-thin"])
    record = read("ls-thin")
    log.setdefault("audits", {})["ls-thin"] = record
    save(log)
    assert record["status"] == "RESOLVED" and record["result"]["verdict"] == "INCONCLUSIVE", record

    # 5a: response-window guard — early resolve MUST revert. The audit uses a
    # 1h dispute window; we first wait out the 300s challenge period so the
    # revert reason is provably the DISPUTE WINDOW (challenge already over),
    # deterministic under any consensus delay.
    audit("guard", "ls-guard", "subject-ok.md", SUBJECT_OK, window=3600, challenge=300)
    write("guard-mark", "open_dispute", ["ls-guard"])
    record = read("ls-guard")
    assert record["status"] == "DISPUTED" and record["dispute_deadline"] > 0, record
    wait_until(deadline_of("ls-guard", "challenge_deadline"), "ls-guard challenge end")
    write("guard-early", "resolve", ["ls-guard"], expected_success=False)
    record = read("ls-guard")
    assert record["status"] == "DISPUTED", record

    # 5b: dispute evidence + post-window resolution (60s minimum window,
    # 300s challenge period; wait covers BOTH deadlines before resolving).
    audit("disp2", "ls-dispute2", "subject-ok.md", SUBJECT_OK, window=60, challenge=300)
    if read("ls-dispute2")["status"] == "OPEN":  # idempotent: an earlier uncertain send may have landed
        write("disp2-mark", "open_dispute", ["ls-dispute2"])
    record = read("ls-dispute2")
    assert record["status"] == "DISPUTED" and record["dispute_deadline"] > 0, record
    write("disp2-ev", "add_dispute_evidence", ["ls-dispute2", pinned("dispute-rebuttal.md"), sha(EV_REBUTTAL)])
    wait_until(max(deadline_of("ls-dispute2", "dispute_deadline"),
                   deadline_of("ls-dispute2", "challenge_deadline")),
               "ls-dispute2 window + challenge end")
    write("disp2-resolve", "resolve", ["ls-dispute2"])
    record = read("ls-dispute2")
    log.setdefault("audits", {})["ls-dispute2"] = record
    save(log)
    assert record["status"] == "RESOLVED", record

    log["smoke_complete"] = True
    save(log)
    print("LIVE_SMOKE_PASS", flush=True)


if __name__ == "__main__":
    run()
