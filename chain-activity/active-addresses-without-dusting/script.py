# Daily unique token recipients on any HyperSync chain, before and after filtering out dusting.
# Reads every ERC-20 and ERC-721 Transfer log with Envio HyperSync, one UTC day at a time.
# A contract counts as a duster on a given day when it sends one transfer per recipient
# (almost every transfer goes to a new address) in large batches (many transfers per transaction)
# to a large number of addresses. Those transfers are dropped and the recipients are counted again.
# Python 3 standard library only. Set ENVIO_API_TOKEN and CHAIN first.
#   CHAIN=<chain> python script.py                              # last 14 full UTC days
#   CHAIN=<chain> START=2026-10-26 END=2026-11-08 python script.py
# CHAIN is the HyperSync network name, the subdomain in https://<chain>.hypersync.xyz.
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, timedelta, timezone

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # Transfer(address,address,uint256)
ZERO = bytes(20)

TOKEN = os.environ.get("ENVIO_API_TOKEN")
CHAIN = os.environ.get("CHAIN")
# Filter thresholds, per contract per day. Tune them for your chain.
MIN_PER_TX = float(os.environ.get("MIN_PER_TX", "20"))         # average transfers per transaction
MIN_UNIQUE_SHARE = float(os.environ.get("MIN_UNIQUE_SHARE", "0.99"))  # unique recipients / transfers
MIN_RECIPIENTS = int(os.environ.get("MIN_RECIPIENTS", "10000"))  # unique recipients that day
WORKERS = int(os.environ.get("WORKERS", "2"))
TOP = int(os.environ.get("TOP", "0"))  # also print the biggest contracts that were kept, to check the rule


def query(body):
    url = f"https://{CHAIN}.hypersync.xyz/query"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def height():
    return json.load(urllib.request.urlopen(f"https://{CHAIN}.hypersync.xyz/height"))["height"]


def block_time(n):
    res = query({"from_block": n, "to_block": n + 1, "include_all_blocks": True,
                 "field_selection": {"block": ["number", "timestamp"]}})
    for batch in res["data"]:
        for b in batch.get("blocks") or []:
            if b["number"] == n:
                t = b["timestamp"]
                return int(t, 16) if isinstance(t, str) else t
    raise RuntimeError(f"no block {n}")


def first_block_at(ts, hi):
    """First block with a timestamp at or after ts (binary search)."""
    lo = 0
    while lo < hi:
        mid = (lo + hi) // 2
        if block_time(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def one_day(job):
    day, start, end = job
    per_contract = defaultdict(set)     # contract -> recipients
    transfers = defaultdict(int)        # contract -> transfer count
    txs = defaultdict(set)              # contract -> transactions
    body = {"from_block": start, "to_block": end, "logs": [{"topics": [[TRANSFER]]}],
            "field_selection": {"log": ["block_number", "transaction_index", "address", "topic0", "topic2"]}}
    while True:
        res = query(body)
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                if log.get("topic0") != TRANSFER or not log.get("topic2"):
                    continue
                to = bytes.fromhex(log["topic2"][-40:])
                if to == ZERO:
                    continue
                c = log["address"].lower()
                per_contract[c].add(to)
                transfers[c] += 1
                txs[c].add((log["block_number"], log["transaction_index"]))
        nb = res["next_block"]
        if nb >= end:
            break
        body["from_block"] = nb
    dusters = []
    for c, rec in per_contract.items():
        n, t = transfers[c], len(txs[c])
        if len(rec) >= MIN_RECIPIENTS and n / t >= MIN_PER_TX and len(rec) / n >= MIN_UNIQUE_SHARE:
            dusters.append((c, len(rec), n, t))
    flagged = {c for c, *_ in dusters}
    kept = set()
    for c, rec in per_contract.items():
        if c not in flagged:
            kept |= rec
    filtered = len(kept)
    for c in flagged:
        kept |= per_contract[c]
    total = sum(transfers.values())
    rest = sorted((c for c in per_contract if c not in flagged), key=lambda c: -len(per_contract[c]))[:TOP]
    rest = [(c, len(per_contract[c]), transfers[c], len(txs[c])) for c in rest]
    return day, dict(transfers=total, raw=len(kept), filtered=filtered,
                     dusters=sorted(dusters, key=lambda d: -d[1]), biggest_kept=rest)


def main():
    if not TOKEN:
        sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
    if not CHAIN:
        sys.exit("Set CHAIN to a HyperSync network name, e.g. the subdomain in https://<chain>.hypersync.xyz")
    today = datetime.now(timezone.utc).date()
    end_day = date.fromisoformat(os.environ["END"]) if "END" in os.environ else today - timedelta(days=1)
    start_day = date.fromisoformat(os.environ["START"]) if "START" in os.environ else end_day - timedelta(days=13)
    days = [start_day + timedelta(days=i) for i in range((end_day - start_day).days + 1)]
    h = height()
    edges = [first_block_at(int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()), h)
             for d in days + [end_day + timedelta(days=1)]]
    jobs = [(str(d), edges[i], edges[i + 1]) for i, d in enumerate(days)]
    print(f"{CHAIN}: every Transfer log, {days[0]} to {days[-1]} (UTC), blocks {edges[0]:,} to {edges[-1] - 1:,}")
    print(f"duster rule per contract per day: >= {MIN_RECIPIENTS:,} recipients, >= {MIN_PER_TX:g} transfers per tx, "
          f">= {MIN_UNIQUE_SHARE:.0%} of transfers to a new address\n")
    print(f"{'day':<12}{'transfers':>12}{'recipients':>13}{'without dusting':>17}{'dusters':>9}")
    results = {}
    with ProcessPoolExecutor(WORKERS) as pool:
        for day, r in pool.map(one_day, jobs):
            results[day] = r
            print(f"{day:<12}{r['transfers']:>12,}{r['raw']:>13,}{r['filtered']:>17,}{len(r['dusters']):>9}", flush=True)
            for c, rec, n, t in r["dusters"]:
                print(f"    dropped {c}  {rec:>10,} recipients  {n:>10,} transfers  {t:>6,} txs  ~{n / t:,.0f} per tx")
            for c, rec, n, t in r["biggest_kept"]:
                print(f"    kept    {c}  {rec:>10,} recipients  {n:>10,} transfers  {t:>6,} txs  ~{n / t:,.0f} per tx")
    peak = max(results, key=lambda d: results[d]["raw"])
    first = results[days[0].isoformat()]
    print(f"\nbusiest day {peak}: {results[peak]['raw']:,} recipients, {results[peak]['filtered']:,} without dusting")
    print(f"first day {days[0]}: {first['raw']:,} recipients, {first['filtered']:,} without dusting")
    out = os.environ.get("OUT")
    if out:
        json.dump(results, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
