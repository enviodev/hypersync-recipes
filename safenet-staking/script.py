"""Safenet staking on Ethereum: SAFE staked, active stakers week by week, and rewards claimed.

Reads every event from Safenet's Staking contract and its reward distribution contract on Ethereum with
Envio HyperSync. Contract addresses come from Safe's docs:
https://docs.safefoundation.org/safenet-aegis/resources/contracts-and-audits
Python 3 standard library only. Set ENVIO_API_TOKEN first.
"""
import collections, json, os, sys, time, urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
URL = "https://1.hypersync.xyz/query"
STAKING = "0x115E78f160e1E3eF163B05C84562Fa16fA338509"
REWARDS = "0xe5139Fc0FB8eae81e30d8a85C22E88c6757120f2"
# topic0 = keccak256 of each event signature
STAKE_TOPIC = "0x835b6b05d09416215e9d638808ff68a75b79bb61e485812125e29950d722de5e"     # StakeIncreased(address,address,uint256)
WITHDRAW_TOPIC = "0xe77a460de02956e5b769dc1b86f3dedb6471a5a1480b18e5e60c025d3842a134"  # WithdrawalInitiated(address,address,uint64,uint256)
CLAIMED_TOPIC = "0xd8138f8a3f377c5259ca548e70e4c2de94f129f5a11036a15b69513cba2b426a"   # Claimed(address,uint256)
E = 10**18


def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer " + TOKEN, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    for attempt in range(10):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def logs(address, topic0s, start):
    out, blocks, fb = [], {}, start
    while True:
        r = post({"from_block": fb, "logs": [{"address": [address], "topics": [topic0s]}],
                  "field_selection": {"log": ["block_number", "log_index", "address", "data", "topic0", "topic1", "topic2"],
                                      "block": ["number", "timestamp"]}})
        for d in r["data"]:
            out += d.get("logs") or []
            for b in d.get("blocks") or []:
                blocks[b["number"]] = int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
        if r["next_block"] >= r["archive_height"]:
            break
        fb = r["next_block"]
    for l in out:
        l["ts"] = blocks[l["block_number"]]
    return sorted(out, key=lambda l: (l["block_number"], l["log_index"])), r["archive_height"]


def addr(topic):
    return "0x" + topic[-40:].lower()


def main():
    staking, head = logs(STAKING, [STAKE_TOPIC, WITHDRAW_TOPIC], 24_585_750)
    rewards, _ = logs(REWARDS, [CLAIMED_TOPIC], 24_749_707)

    per = collections.defaultdict(int)
    total = 0
    weekly = {}
    for l in staking:
        staker = addr(l["topic1"])
        amount = int(l["data"][-64:], 16)
        if l["topic0"] == STAKE_TOPIC:
            per[staker] += amount; total += amount
        else:
            per[staker] -= amount; total -= amount
        week = datetime.fromtimestamp(l["ts"], timezone.utc).strftime("%G-W%V")
        weekly[week] = (total, sum(1 for v in per.values() if v > 0))

    claimed = sum(int(l["data"][-64:], 16) for l in rewards)
    claimers = {addr(l["topic1"]) for l in rewards}
    active = sum(1 for v in per.values() if v > 0)

    print(f"Safenet staking on Ethereum, up to block {head:,}")
    print(f"  SAFE staked: {total / E:,.0f} ({100 * total / (10**9 * E):.2f}% of the 1B SAFE supply)")
    print(f"  Active stakers: {active:,}")
    print(f"  SAFE rewards claimed so far: {claimed / E:,.0f} by {len(claimers):,} wallets")
    print("Week by week (SAFE staked, active stakers):")
    for w, (t, n) in weekly.items():
        print(f"  {w}  {t / E:>12,.0f}  {n:>4}")


if __name__ == "__main__":
    main()
