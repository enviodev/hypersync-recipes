"""Weekly USDC deposits and borrows on Aave V3 Ethereum.

Reads every Supply, Withdraw, Borrow and Repay event for USDC on the Aave V3 Ethereum Pool
with Envio HyperSync, buckets them into 7-day weeks ending at the latest block, and prints
net deposits (Supply minus Withdraw) and net borrows (Borrow minus Repay) for each week.
"""
import collections, datetime, json, os, sys, time, urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN")
HS = "https://eth.hypersync.xyz"
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"  # Aave V3 Ethereum Pool (bgd-labs/aave-address-book)
USDC = "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # reserve, as topic1
EVENTS = {
    "0x2b627736bca15cd5381dcf80b0bf11fd197d01a037c52b927a881a10fb73ba61": "Supply",
    "0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7": "Withdraw",
    "0xb3d084820fb1a9decffb176436bd02558d15fac9b0ddfed8c465bc7359d7dce0": "Borrow",
    "0xa534c8dbe71f871f9f3530e97a74601fea17b426cae02e1c5aee42c96c784051": "Repay",
}
WEEKS = int(sys.argv[1]) if len(sys.argv) > 1 else 52
START = 23_780_000  # about 12 Nov 2025; move it back for more weeks


def post(body):
    for attempt in range(15):
        try:
            req = urllib.request.Request(HS + "/query", json.dumps(body).encode(),
                                         {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(5 * (attempt + 1))  # back off on rate limits
    raise SystemExit("HyperSync request failed")


def amount(log, ev):
    data = log["data"][2:]
    # Supply and Borrow have (user, amount, ...) in data; Withdraw and Repay start with amount
    return int(data[64:128], 16) / 1e6 if ev in ("Supply", "Borrow") else int(data[0:64], 16) / 1e6


rows, block_ts = [], {}
body = {"from_block": START,
        "logs": [{"address": [POOL], "topics": [list(EVENTS), [USDC]]}],
        "field_selection": {"log": ["address", "topic0", "topic1", "data", "block_number"],
                            "block": ["number", "timestamp"]}}
while True:
    r = post(body)
    for batch in r["data"]:
        for b in batch.get("blocks") or []:
            ts = b["timestamp"]
            block_ts[b["number"]] = int(ts, 16) if isinstance(ts, str) else ts
        for log in batch.get("logs") or []:
            # default join only; keep exactly the pool, event and reserve we asked for
            if log["address"].lower() == POOL and log["topic0"] in EVENTS and log["topic1"] == USDC:
                rows.append(log)
    if r["next_block"] >= r["archive_height"]:
        break
    body["from_block"] = r["next_block"]

end = max(block_ts.values())
supply, borrow = collections.Counter(), collections.Counter()
for log in rows:
    ev = EVENTS[log["topic0"]]
    week = (end - block_ts[log["block_number"]]) // (7 * 86400)  # 0 = most recent week
    if week >= WEEKS:
        continue
    a = amount(log, ev)
    if ev == "Supply": supply[week] += a
    if ev == "Withdraw": supply[week] -= a
    if ev == "Borrow": borrow[week] += a
    if ev == "Repay": borrow[week] -= a

day = lambda w: datetime.datetime.fromtimestamp(end - w * 7 * 86400, datetime.timezone.utc).strftime("%d %b %Y")
print(f"Aave V3 Ethereum, USDC, {len(rows):,} events, weeks ending {day(0)} {datetime.datetime.fromtimestamp(end, datetime.timezone.utc):%H:%M} UTC")
print("Top 5 weeks by net deposits:")
for w, v in sorted(supply.items(), key=lambda kv: -kv[1])[:5]:
    print(f"  week to {day(w)}   deposits {v/1e6:+8.1f}M   borrows {borrow[w]/1e6:+8.1f}M")
s, b = supply[0], borrow[0]
print(f"Latest week: {s/1e6:+.1f}M deposited, {b/1e6:+.1f}M borrowed ({100*b/s:.0f}% of the new deposits)" if s > 0 else "")
