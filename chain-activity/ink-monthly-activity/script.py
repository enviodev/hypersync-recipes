# Ink transactions and active addresses by month in 2026, with Envio HyperSync.
# Reads every Ink transaction since 1 January 2026 (from and type only), buckets it by its block's UTC month,
# and counts transactions plus unique senders per month.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import concurrent.futures
import datetime
import json
import os
import sys
import time
import urllib.request

BASE = "https://ink.hypersync.xyz"  # Ink mainnet, chain ID 57073
YEAR = 2026
CHUNK, WORKERS = 100000, 12
DEPOSIT_TYPE = 126  # 0x7e, OP Stack deposit transactions, including the L1 info transaction every block

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def block_time(n):
    res = post("/query", {"from_block": n, "to_block": n + 1, "include_all_blocks": True,
                          "field_selection": {"block": ["number", "timestamp"]}})
    for batch in res["data"]:
        for b in batch.get("blocks") or []:
            return int(b["timestamp"], 16)


def first_block_at(ts, hi):
    lo = 0
    while lo < hi:
        mid = (lo + hi) // 2
        if block_time(mid) >= ts:
            hi = mid
        else:
            lo = mid + 1
    return lo


def scan(lo, hi, month):
    """Counts and unique senders for blocks [lo, hi), all in one month."""
    txs, deposits, senders = 0, 0, set()
    body = {"from_block": lo, "to_block": hi, "transactions": [{}],
            "field_selection": {"transaction": ["from", "type"]}}
    while True:
        res = post("/query", body)
        for batch in res["data"]:
            for t in batch.get("transactions") or []:
                txs += 1
                if t["type"] == DEPOSIT_TYPE:
                    deposits += 1
                else:
                    senders.add(t["from"])
        if res["next_block"] >= hi:
            break
        body["from_block"] = res["next_block"]
    return month, txs, deposits, senders


# END_BLOCK pins the run to a fixed block (exclusive) so the numbers can be reproduced. Default is the chain head.
head = int(os.environ.get("END_BLOCK") or post("/height")["height"])
end = datetime.datetime.fromtimestamp(block_time(head - 1), datetime.timezone.utc)
months, starts = [], []
for m in range(1, end.month + 1):
    ts = int(datetime.datetime(YEAR, m, 1, tzinfo=datetime.timezone.utc).timestamp())
    months.append(f"{YEAR}-{m:02d}")
    starts.append(first_block_at(ts, head))
starts.append(head)  # the last month runs to the end block
print("Month start blocks:", dict(zip(months, starts)), file=sys.stderr)

# The last month is also split by UTC day, so you can see its daily pace
days, day_starts = [], []
for d in range(1, end.day + 1):
    ts = int(datetime.datetime(YEAR, end.month, d, tzinfo=datetime.timezone.utc).timestamp())
    days.append(f"{YEAR}-{end.month:02d}-{d:02d}")
    day_starts.append(first_block_at(ts, head))
day_starts.append(head)

jobs = []
for i, month in enumerate(months[:-1]):
    for a in range(starts[i], starts[i + 1], CHUNK):
        jobs.append((a, min(a + CHUNK, starts[i + 1]), month))
for i, day in enumerate(days):
    for a in range(day_starts[i], day_starts[i + 1], CHUNK):
        jobs.append((a, min(a + CHUNK, day_starts[i + 1]), day))

txs, deposits, senders = collections.Counter(), collections.Counter(), collections.defaultdict(set)
day_txs = collections.Counter()
all_senders = set()
with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
    for i, (key, n, d, s) in enumerate(pool.map(lambda j: scan(*j), jobs)):
        month = key[:7]
        if len(key) > 7:
            day_txs[key] += n - d
        txs[month] += n
        deposits[month] += d
        senders[month] |= s
        all_senders |= s
        print(f"  {i + 1}/{len(jobs)} chunks", file=sys.stderr)

print(f"Ink, 1 Jan {YEAR} to block {head:,} ({end:%Y-%m-%d %H:%M} UTC)")
print(f"{'month':8} {'all txs':>13} {'user txs':>13} {'deposit txs':>12} {'active addresses':>17}")
for m in months:
    print(f"{m:8} {txs[m]:13,} {txs[m] - deposits[m]:13,} {deposits[m]:12,} {len(senders[m]):17,}")
T, D = sum(txs.values()), sum(deposits.values())
print(f"{'total':8} {T:13,} {T - D:13,} {D:12,} {len(all_senders):17,} unique over the whole period")
print(f"User transactions per UTC day in {months[-1]} (the last day may be partial)")
for d in days:
    print(f"  {d}  {day_txs[d]:11,}")
json.dump({"end_block": head, "days": {d: day_txs[d] for d in days}, "start_blocks": dict(zip(months, starts)),
           "months": {m: {"txs": txs[m], "user_txs": txs[m] - deposits[m], "deposit_txs": deposits[m],
                          "active_addresses": len(senders[m])} for m in months},
           "unique_senders_ytd": len(all_senders)}, open("ink_monthly.json", "w"), indent=1)
