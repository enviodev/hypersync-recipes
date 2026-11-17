# How Monad handled a volatile market day, against its previous 30 days, with Envio HyperSync.
# Reads every block and every transaction on Monad for one UTC day plus the 30 days before it,
# then compares the day's hours with the baseline: transactions, block times, gas used and base fee.
# Default day is 10 November 2026, when a hotter than expected US CPI print (13:30 UTC) hit crypto prices.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import calendar
import collections
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HYPERSYNC = "https://monad.hypersync.xyz"
DAY = sys.argv[1] if len(sys.argv) > 1 else "2026-11-10"
BASELINE_DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
CHUNK = 20000  # blocks per parallel range

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def get(path, body=None):
    req = urllib.request.Request(HYPERSYNC + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(10):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception:
            time.sleep(3 * (attempt + 1))  # also covers HyperSync's per-minute rate limit
    sys.exit("Request kept failing: " + path)


def block_time(n):
    res = get("/query", {"from_block": n, "to_block": n + 1, "include_all_blocks": True,
                         "field_selection": {"block": ["timestamp"]}})
    return int(res["data"][0]["blocks"][0]["timestamp"], 16)


def first_block_at(ts, lo, hi):
    while lo < hi:
        mid = (lo + hi) // 2
        lo, hi = (mid + 1, hi) if block_time(mid) < ts else (lo, mid)
    return lo


# 1. Block range: BASELINE_DAYS full UTC days before DAY, then DAY itself
day_start = calendar.timegm(time.strptime(DAY, "%Y-%m-%d"))
t0, t1 = day_start - BASELINE_DAYS * 86400, day_start + 86400
head = get("/height")["height"] - 1
if block_time(head) < t1:
    sys.exit(DAY + " has not finished yet on Monad")
start = first_block_at(t0, 1, head)
end = first_block_at(t1, start, head)  # first block of the next day, not included

# 2. Every block and transaction, bucketed by UTC hour (and by minute for transactions)
# hour -> [blocks, transactions, failed transactions, gas used, gas limit]
hours = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
minutes = collections.Counter()
base_fees = collections.defaultdict(collections.Counter)  # hour -> base fee (wei) -> blocks
lock = threading.Lock()


def scan(first):
    last = min(first + CHUNK, end)
    body = {"from_block": first, "to_block": last, "include_all_blocks": True, "transactions": [{}],
            "field_selection": {"block": ["number", "timestamp", "gas_used", "gas_limit", "base_fee_per_gas"],
                                "transaction": ["block_number", "status"]}}
    h, m, bf, ts = collections.defaultdict(lambda: [0, 0, 0, 0, 0]), collections.Counter(), \
        collections.defaultdict(collections.Counter), {}
    while True:
        res = get("/query", body)
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                t = int(b["timestamp"], 16)
                ts[b["number"]] = t
                row = h[t // 3600 * 3600]
                row[0] += 1
                row[3] += int(b["gas_used"], 16)
                row[4] += int(b["gas_limit"], 16)
                bf[t // 3600 * 3600][int(b.get("base_fee_per_gas") or "0x0", 16)] += 1
        for batch in res["data"]:
            for tx in batch.get("transactions") or []:
                t = ts.get(tx["block_number"]) or block_time(tx["block_number"])
                row = h[t // 3600 * 3600]
                row[1] += 1
                row[2] += tx.get("status") == 0
                m[t // 60 * 60] += 1
        if res["next_block"] >= last:
            break
        body["from_block"] = res["next_block"]
    with lock:
        for k, v in h.items():
            hours[k] = [a + b for a, b in zip(hours[k], v)]
        minutes.update(m)
        for k, v in bf.items():
            base_fees[k].update(v)


with ThreadPoolExecutor(12) as pool:
    list(pool.map(scan, range(start, end, CHUNK)))


# 3. Compare the day with the baseline
def median(counter):
    total, seen = sum(counter.values()), 0
    for value in sorted(counter):
        seen += counter[value]
        if seen * 2 >= total:
            return value


def hhmm(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%d %b %H:%M")


base = {k: v for k, v in hours.items() if k < day_start}
day = {k: v for k, v in hours.items() if k >= day_start}
base_tx_per_hour = sum(v[1] for v in base.values()) / len(base)
base_busiest = max(base, key=lambda k: base[k][1])
base_fill = sum(v[3] for v in base.values()) / sum(v[4] for v in base.values())
base_block_s = 3600 * len(base) / sum(v[0] for v in base.values())
base_fail = sum(v[2] for v in base.values()) / sum(v[1] for v in base.values())
peak = max(day, key=lambda k: day[k][1])
peak_min = max((k for k in minutes if k >= day_start), key=lambda k: minutes[k])
base_peak_min = max((k for k in minutes if k < day_start), key=lambda k: minutes[k])

print(f"Monad, blocks {start} to {end - 1}: {BASELINE_DAYS} days before {DAY} (baseline), then {DAY}\n")
print(f"Baseline: {base_tx_per_hour:,.0f} transactions an hour on average, "
      f"busiest hour {hhmm(base_busiest)} UTC with {base[base_busiest][1]:,}")
print(f"          busiest minute {hhmm(base_peak_min)} UTC with {minutes[base_peak_min]:,} "
      f"({minutes[base_peak_min] / 60:,.0f} TPS)")
print(f"          one block every {base_block_s:.3f}s, blocks {base_fill:.1%} full on average, "
      f"{base_fail:.2%} of transactions reverted\n")
print(f"{DAY} by hour (UTC)")
print("  hour    transactions  vs baseline  blocks  block time  gas used  median base fee  max base fee  reverted")
for k in sorted(day):
    b, tx, failed, used, limit = day[k]
    print(f"  {hhmm(k)[-5:]}   {tx:>12,}  {tx / base_tx_per_hour:>10.1f}x  {b:>6,}  {3600 / b:>9.3f}s  "
          f"{used / limit:>8.1%}  {median(base_fees[k]) / 1e9:>11.1f} gwei  {max(base_fees[k]) / 1e9:>8.1f} gwei  "
          f"{failed / tx:>8.2%}")
b, tx, failed, used, limit = day[peak]
print(f"\nBusiest hour: {hhmm(peak)} UTC, {tx:,} transactions, {tx / base_tx_per_hour:.1f}x the baseline hourly average"
      f" and {tx / base[base_busiest][1]:.1f}x the baseline's busiest hour")
print(f"  blocks every {3600 / b:.3f}s (baseline {base_block_s:.3f}s), "
      f"median base fee {median(base_fees[peak]) / 1e9:.1f} gwei")
print(f"Busiest minute: {hhmm(peak_min)} UTC, {minutes[peak_min]:,} transactions ({minutes[peak_min] / 60:,.0f} TPS)")
