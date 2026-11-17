# Where Polygon PoS gas fees came from in October 2026, with Envio HyperSync.
# Reads every October transaction (to, gas_used, effective_gas_price) and every block (gas_used, base fee),
# then ranks destination contracts by the gas fees their transactions paid, in POL.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import concurrent.futures
import datetime
import json
import os
import re
import sys
import time
import urllib.request

URL = "https://polygon.hypersync.xyz/query"
START, END = 94738440, 96523829  # first blocks at 2026-10-01 00:00 UTC and 2026-11-01 00:00 UTC (end exclusive)
CHUNK, WORKERS = 20000, 12
# Verified names only. Polymarket addresses come from Polymarket's docs
# (https://docs.polymarket.com/developers/CTF/deployment-resources) plus the Relay Hub, which Polygonscan labels
# "Polymarket: Relay Hub". The rest are Polygonscan labels. Everything else stays unlabelled.
POLYMARKET = {
    "0xe111180000d2663c0091e4f400237545b87b996b": "CTF Exchange V2",
    "0xe2222d279d744050d28e00520010520000310f59": "Neg Risk CTF Exchange V2",
    "0x00000000000fb5c9adea0298d729a0cb3823cc07": "Deposit Wallet Factory",
    "0xd216153c06e857cd7f72665e0af1d7d82172f494": "Relay Hub",
    "0xe3333700ca9d93003f00f0f71f8515005f6c00aa": "Exchange V3",
}
POLYMARKET_DOCS = "https://docs.polymarket.com/developers/CTF/deployment-resources"
LABELS = {
    "0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff": "QuickSwap V2 Router",
    "0xca11bde05977b3631167028862be2a173976ca11": "Multicall3",
    "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "Circle USDC",
    "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "Circle USDC.e",
    "0x3c4829196bfadff4394726b45159aeaac6fcd41c": "OKX DEX Router",
    "0x4337084d9e255ff0702461cf8895ce9e3b5ff108": "ERC-4337 EntryPoint 0.8",
    "0x0000000071727de22e5e9d8baf0edac6f37da032": "ERC-4337 EntryPoint 0.7",
    "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": "USDT0",
}

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def scan(lo, hi):
    """Fees per destination and per day for blocks [lo, hi)."""
    fees, txs, day_fee, burn, ts = collections.Counter(), collections.Counter(), collections.Counter(), 0, {}
    body = {"from_block": lo, "to_block": hi, "include_all_blocks": True, "transactions": [{}],
            "max_num_transactions": 100000,
            "field_selection": {"transaction": ["block_number", "to", "gas_used", "effective_gas_price"],
                                "block": ["number", "timestamp", "gas_used", "base_fee_per_gas"]}}
    while True:
        res = post(body)
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                ts[int(b["number"], 16) if isinstance(b["number"], str) else b["number"]] = int(b["timestamp"], 16)
                burn += int(b["gas_used"], 16) * int(b.get("base_fee_per_gas") or "0x0", 16)
            for t in batch.get("transactions") or []:
                fee = int(t["gas_used"], 16) * int(t["effective_gas_price"], 16)
                to = t.get("to") or "contract creation"
                fees[to] += fee
                txs[to] += 1
                bn = t["block_number"]
                bn = int(bn, 16) if isinstance(bn, str) else bn
                day_fee[bn] += fee
        if res["next_block"] >= hi:
            break
        body["from_block"] = res["next_block"]
    days = collections.Counter()
    for bn, f in day_fee.items():
        days[datetime.datetime.fromtimestamp(ts[bn], datetime.timezone.utc).strftime("%Y-%m-%d")] += f
    return fees, txs, days, burn


fees, txs, days, burn = collections.Counter(), collections.Counter(), collections.Counter(), 0
ranges = [(a, min(a + CHUNK, END)) for a in range(START, END, CHUNK)]
with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
    for i, (f, n, d, b) in enumerate(pool.map(lambda r: scan(*r), ranges)):
        fees.update(f); txs.update(n); days.update(d); burn += b
        print(f"  {i + 1}/{len(ranges)} chunks", file=sys.stderr)

# Every Polygon address in Polymarket's docs counts toward Polymarket too
try:
    page = urllib.request.urlopen(urllib.request.Request(POLYMARKET_DOCS, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode()
    for a in set(re.findall(r"0x[0-9a-fA-F]{40}", page)):
        POLYMARKET.setdefault(a.lower(), "listed in Polymarket docs")
except Exception:
    print("Could not read Polymarket's docs, using the five core contracts only", file=sys.stderr)
for a, n in POLYMARKET.items():
    LABELS[a] = "Polymarket " + n
total = sum(fees.values())
print(f"Polygon PoS, October 2026: {sum(txs.values()):,} transactions paid {total / 1e18:,.0f} POL in gas fees")
print(f"  base fee part {burn / 1e18:,.0f} POL, priority fee part {(total - burn) / 1e18:,.0f} POL")
print("Top destinations by share of fees")
for to, f in fees.most_common(25):
    print(f"  {to:42} {LABELS.get(to, ''):32} {f / 1e18:12,.0f} POL {100 * f / total:6.2f}%  {txs[to]:>11,} txs")
pm = sum(f for a, f in fees.items() if a in POLYMARKET)
usdc = sum(fees[a] for a in ("0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"))
print("By app")
print(f"  Polymarket, {sum(1 for a in fees if a in POLYMARKET)} contracts   {pm / 1e18:12,.0f} POL {100 * pm / total:6.2f}%")
print(f"  QuickSwap V2 Router            {fees['0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff'] / 1e18:12,.0f} POL "
      f"{100 * fees['0xa5e0829caced8ffdd4de3c43696c57f7d7a678ff'] / total:6.2f}%")
print(f"  Circle USDC and USDC.e         {usdc / 1e18:12,.0f} POL {100 * usdc / total:6.2f}%")
json.dump({"total": str(total), "burn": str(burn), "fees": {k: str(v) for k, v in fees.most_common(200)},
           "txs": dict(txs.most_common(200)), "days": {k: str(v) for k, v in sorted(days.items())}},
          open("polygon_october_fees.json", "w"), indent=1)
