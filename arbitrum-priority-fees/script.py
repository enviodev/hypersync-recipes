"""Every priority fee paid on Arbitrum One, pulled with Envio HyperSync.

Arbitrum One started collecting priority fees on 23 Sep 2026 (ArbOS 61, priority gas auctions). Since then
a transaction can pay a tip on top of the base fee to be ordered first.

This script reads every transaction (gas_used, effective_gas_price) and every block's base fee since
that day. A transaction paid a priority fee when its effective gas price is above its block's base fee,
and the fee is (effective gas price - base fee) x gas used. It prints, per UTC day, how many transactions
there were, how many paid a priority fee and how much ETH those fees came to.

Dollar values come from HyperSync too. The script reads the AnswerUpdated logs of the Chainlink ETH/USD
aggregator on Arbitrum for the same blocks and prices each day's fees at that UTC day's average answer.

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
# Chainlink ETH / USD on Arbitrum One: the feed proxy 0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612 (8 decimals, see its
# description() and aggregator()) and the aggregator behind it, which emits AnswerUpdated.
ETH_USD_AGGREGATOR = "0xd827123d014578c965f6c9d87a641ec05faa5501"
ETH_USD_PROXY = "0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612"
ANSWER_UPDATED = "0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f"  # AnswerUpdated(int256 indexed current, uint256 indexed roundId, uint256 updatedAt)


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


def eth_usd_by_day(lo, hi):
    """Average Chainlink ETH/USD answer per UTC day for blocks [lo, hi), read with HyperSync. The last answer before lo
    is included so a day with no update still has a price. Returns (a function from a day string to a price, count of answers, last answer)."""
    answers, start = [], max(lo - 2_000_000, 0)
    body = {"from_block": start, "to_block": hi,
            "logs": [{"address": [ETH_USD_AGGREGATOR], "topics": [[ANSWER_UPDATED]]}],
            "field_selection": {"log": ["address", "topic0", "topic1", "data"]}}
    while True:
        res = post(body)
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                if log["address"].lower() == ETH_USD_AGGREGATOR and log["topic0"] == ANSWER_UPDATED:
                    answers.append((int(log["data"], 16), int(log["topic1"], 16) / 1e8))
        if res["next_block"] >= hi:
            break
        body["from_block"] = res["next_block"]
    answers.sort()
    per_day = collections.defaultdict(list)
    for t, p in answers:
        per_day[datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")].append(p)
    days = sorted(per_day)

    def price(day):
        if day in per_day:
            return sum(per_day[day]) / len(per_day[day])
        earlier = [d for d in days if d < day]
        return sum(per_day[earlier[-1]]) / len(per_day[earlier[-1]]) if earlier else per_day[days[0]][0]
    return price, len(answers), answers[-1][1]


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
    eth_usd, n_answers, last_answer = eth_usd_by_day(FROM_BLOCK, head)
    print(f"Arbitrum One, blocks {FROM_BLOCK:,} to {head:,}")
    print("day         transactions  with priority fee  share   fees (ETH)  ETH/USD   fees (USD)  running total")
    running, usd_total = 0, 0.0
    for d in sorted(days):
        total, tipped, wei = days[d]
        running += tipped
        usd = wei / 1e18 * eth_usd(d)
        usd_total += usd
        print(f"{d}  {total:>12,}  {tipped:>17,}  {tipped / total:>5.0%}  {wei / 1e18:>10.2f}  {eth_usd(d):>7,.0f}  {usd:>11,.0f}  {running:>13,}")
    tipped = sum(v[1] for v in days.values())
    print(f"\ntransactions with a priority fee  {tipped:,}")
    print(f"priority fees                     {sum(v[2] for v in days.values()) / 1e18:,.2f} ETH")
    print(f"priority fees in dollars          ${usd_total:,.0f} at each day's average Chainlink ETH/USD answer ({n_answers:,} AnswerUpdated logs read with HyperSync)")
    # Check, labelled: the same feed's latest answer over Arbitrum's public RPC, for a scan that runs to the chain head
    try:
        if TO_BLOCK:
            raise ValueError("only run for a scan up to the chain head, because the public RPC does not serve old state")
        req = urllib.request.Request("https://arb1.arbitrum.io/rpc", json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [
            {"to": ETH_USD_PROXY, "data": "0x50d25bcd"}, "latest"]}).encode(), {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        print(f"Check (Chainlink ETH/USD latestAnswer over RPC): ${int(json.load(urllib.request.urlopen(req, timeout=60))['result'], 16) / 1e8:,.2f}, "
              f"last AnswerUpdated read with HyperSync ${last_answer:,.2f}")
    except Exception as err:
        print("Check (RPC) skipped:", err)
    out = {d: {"transactions": v[0], "with_priority_fee": v[1], "priority_fee_wei": str(v[2]), "eth_usd": round(eth_usd(d), 2)} for d, v in sorted(days.items())}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arbitrum_priority_fees.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
