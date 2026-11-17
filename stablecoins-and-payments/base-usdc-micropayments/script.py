# Gasless USDC payments on Base, sized: every EIP-3009 transferWithAuthorization /
# receiveWithAuthorization on Base USDC in a time window, with Envio HyperSync.
# Prints how many there were, how many were worth a cent or less, and an hourly breakdown.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
#
#   python script.py                        # last 24 hours
#   python script.py 24 2026-11-09T17:07    # 24 hours ending at a UTC time
import collections
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = "https://base.hypersync.xyz"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # native USDC on Base, from developers.circle.com
AUTH_USED = "0x98de503528ee59b575ef0c0a2576a82497bfc029a5685b209e9ec333479b10a5"  # AuthorizationUsed(address,bytes32)
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
HOURS = int(sys.argv[1]) if len(sys.argv) > 1 else 24
END = (int(datetime.datetime.fromisoformat(sys.argv[2]).replace(tzinfo=datetime.timezone.utc).timestamp())
       if len(sys.argv) > 2 else None)


def post(path, body=None):
    for attempt in range(8):
        try:
            req = urllib.request.Request(URL + path, json.dumps(body).encode() if body else None,
                                         {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(5 * (attempt + 1))


def num(v):
    return int(v, 16) if isinstance(v, str) else v


def block_time(b):
    d = post("/query", {"from_block": b, "to_block": b + 1, "include_all_blocks": True,
                        "field_selection": {"block": ["number", "timestamp"]}})
    for x in d["data"]:
        for blk in x.get("blocks", []):
            return num(blk["timestamp"])


def block_at(ts, hi):
    lo = 0
    while lo < hi:
        mid = (lo + hi) // 2
        if block_time(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


height = post("/height")["height"] - 1
end_block = block_at(END, height) if END else height
end_ts = block_time(end_block)
start_block = block_at(end_ts - HOURS * 3600, end_block)

# One query for the AuthorizationUsed logs. JoinAll brings back every log in those
# transactions, so the matching USDC Transfer gives each payment's size.
payers, transfers, times = collections.defaultdict(list), collections.defaultdict(list), {}
block = start_block
while True:
    d = post("/query", {
        "from_block": block, "to_block": end_block,
        "logs": [{"address": [USDC], "topics": [[AUTH_USED]]}],
        "join_mode": "JoinAll",
        "field_selection": {"block": ["number", "timestamp"],
                            "log": ["block_number", "transaction_hash", "address", "topic0", "topic1", "topic2", "data"]},
    })
    for x in d["data"]:
        for b in x.get("blocks", []):
            times[num(b["number"])] = num(b["timestamp"])
        for log in x.get("logs", []):
            if log["address"].lower() != USDC:
                continue
            t0, tx = log["topic0"].lower(), log["transaction_hash"]
            if t0 == AUTH_USED:
                payers[tx].append("0x" + log["topic1"][-40:].lower())
            elif t0 == TRANSFER:
                transfers[tx].append(("0x" + log["topic1"][-40:].lower(), num(log["data"]) / 1e6, num(log["block_number"])))
    if d["next_block"] <= block or d["next_block"] >= end_block:
        break
    block = d["next_block"]

payments = []
for tx, who in payers.items():
    pool = list(transfers.get(tx, []))
    for p in who:
        match = next((t for t in pool if t[0] == p), None)
        if match:
            pool.remove(match)
            payments.append((p, match[1], times.get(match[2])))

small = [p for p in payments if p[1] <= 0.01]
fmt = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
print(f"Base USDC, {fmt(end_ts - HOURS * 3600)} to {fmt(end_ts)} (blocks {start_block:,} to {end_block:,})")
print(f"Gasless USDC payments (AuthorizationUsed): {sum(len(v) for v in payers.values()):,} from {len({p[0] for p in payments}):,} wallets")
print(f"Worth a cent or less: {len(small):,} from {len({p[0] for p in small}):,} wallets, ${sum(p[1] for p in small):,.2f} in total")
print(f"  at $0.001 or less        {sum(1 for p in small if p[1] <= 0.001):,}")
print(f"  between $0.001 and $0.01 {sum(1 for p in small if 0.001 < p[1] < 0.01):,}")
print(f"  at $0.01                 {sum(1 for p in small if p[1] == 0.01):,}")
print("Payments of a cent or less, by hour (UTC)")
hours = collections.Counter(datetime.datetime.fromtimestamp(p[2], datetime.timezone.utc).hour for p in small)
for h in range(24):
    print(f"  {h:02d}:00 {hours[h]:>6,}")
