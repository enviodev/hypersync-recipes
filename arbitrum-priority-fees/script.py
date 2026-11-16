"""Every priority fee paid on Arbitrum One, pulled with Envio HyperSync.

Arbitrum One started collecting priority fees on 23 Sep 2026 (ArbOS 61, priority gas auctions). Since then
a transaction can pay a tip on top of the base fee to be ordered first.

This script reads every transaction (gas_used, effective_gas_price) and every block's base fee since
that day. A transaction paid a priority fee when its effective gas price is above its block's base fee,
and the fee is (effective gas price - base fee) x gas used. It prints, per UTC day, how many transactions
there were, how many paid a priority fee and how much ETH those fees came to.

It is a big scan (about 100M transactions), so it runs in parallel worker processes and takes a while.

Usage:
    export ENVIO_API_TOKEN=your-token
    python script.py
    FROM_BLOCK=524000000 TO_BLOCK=524300000 python script.py     # a smaller range
"""
import collections, datetime, json, os, sys, time, urllib.request
from multiprocessing import Pool

URL = "https://arbitrum.hypersync.xyz"
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (https://envio.dev/app/api-tokens)")
FROM_BLOCK = int(os.environ.get("FROM_BLOCK", 507_945_268))  # first block of 23 Sep 2026 UTC
TO_BLOCK = int(os.environ.get("TO_BLOCK", 0))                # 0 means the chain head
WORKERS = int(os.environ.get("WORKERS", 12))
CHUNK = 50_000


def post(body):
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}
    for attempt in range(30):
        try:
            req = urllib.request.Request(URL + "/query", json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:  # 429s and timeouts: back off and retry
            time.sleep(min(30, 3 * (attempt + 1)))
    raise SystemExit("HyperSync kept failing")


def num(v):
    return int(v, 16) if isinstance(v, str) else (v or 0)


def scan(block_range):
    """Per-day [transactions, transactions with a priority fee, priority fees in wei] for blocks [lo, hi)."""
    lo, hi = block_range
    base, when, txs = {}, {}, []
    body = {"from_block": lo, "to_block": hi, "include_all_blocks": True, "transactions": [{}],
            "field_selection": {"transaction": ["block_number", "gas_used", "effective_gas_price"],
                                "block": ["number", "timestamp", "base_fee_per_gas"]}}
    while True:
        res = post(body)
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                n = num(b["number"])
                base[n] = num(b.get("base_fee_per_gas"))
                when[n] = num(b["timestamp"])
            for t in batch.get("transactions") or []:
                txs.append((num(t["block_number"]), num(t["gas_used"]), num(t["effective_gas_price"])))
        if res["next_block"] >= hi:
            break
        body["from_block"] = res["next_block"]
    days = collections.defaultdict(lambda: [0, 0, 0])
    for block, gas_used, price in txs:
        d = datetime.datetime.fromtimestamp(when[block], datetime.timezone.utc).strftime("%Y-%m-%d")
        days[d][0] += 1
        tip = price - base[block]
        if tip > 0:
            days[d][1] += 1
            days[d][2] += tip * gas_used
    return dict(days)


def main():
    head = TO_BLOCK or int(json.load(urllib.request.urlopen(URL + "/height"))["height"])
    ranges = [(a, min(a + CHUNK, head)) for a in range(FROM_BLOCK, head, CHUNK)]
    days = collections.defaultdict(lambda: [0, 0, 0])
    with Pool(WORKERS) as pool:
        for i, part in enumerate(pool.imap_unordered(scan, ranges)):
            for d, v in part.items():
                for k in range(3):
                    days[d][k] += v[k]
            print(f"  {i + 1}/{len(ranges)} chunks", file=sys.stderr)
    print(f"Arbitrum One, blocks {FROM_BLOCK:,} to {head:,}")
    print("day         transactions  with priority fee  share   fees (ETH)  running total")
    running = 0
    for d in sorted(days):
        total, tipped, wei = days[d]
        running += tipped
        print(f"{d}  {total:>12,}  {tipped:>17,}  {tipped / total:>5.0%}  {wei / 1e18:>10.2f}  {running:>13,}")
    tipped = sum(v[1] for v in days.values())
    print(f"\ntransactions with a priority fee  {tipped:,}")
    print(f"priority fees                     {sum(v[2] for v in days.values()) / 1e18:,.2f} ETH")
    out = {d: {"transactions": v[0], "with_priority_fee": v[1], "priority_fee_wei": str(v[2])} for d, v in sorted(days.items())}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arbitrum_priority_fees.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
