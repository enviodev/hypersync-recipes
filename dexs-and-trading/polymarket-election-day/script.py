"""Polymarket trading volume by hour, read straight from Polygon with Envio HyperSync.

Reproduces the numbers in Envio's US election day post: taker-side USDC traded on
Polymarket's exchange contracts from 00:00 to 12:00 UTC on a given day, compared
with the same hours on each of the six days before it.

Run:
    export ENVIO_API_TOKEN=...   # free token: https://envio.dev/app/api-tokens
    python script.py 2026-11-03
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = "https://polygon.hypersync.xyz/query"
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN first")

# Polymarket exchange contracts on Polygon: docs.polymarket.com/developers/CTF/deployment-resources
EXCHANGES = [
    "0xE111180000d2663C0091e4f400237545B87B996B",  # CTF Exchange
    "0xe2222d279d744050d28e00520010520000310F59",  # Neg Risk CTF Exchange
    "0xe3333700cA9d93003F00f0F71f8515005F6c00Aa",  # Exchange V3
]
ORDERS_MATCHED = "0x174b3811690657c217184f89418266767c87e4805d09680c39fc9c031c0cab7c"


def query(body):
    for attempt in range(10):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {
                "Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(2 + 2 * attempt)
    sys.exit("HyperSync request kept failing")


def block_at(ts):
    """First block at or after a unix timestamp, by binary search."""
    with urllib.request.urlopen(URL.replace("/query", "/height"), timeout=60) as r:
        lo, hi = 0, json.loads(r.read())["height"]
    while lo < hi:
        mid = (lo + hi) // 2
        b = query({"from_block": mid, "to_block": mid + 1, "blocks": [{}],
                   "field_selection": {"block": ["timestamp"]}})["data"][0]["blocks"][0]["timestamp"]
        b = int(b, 16) if isinstance(b, str) else b
        lo, hi = (mid + 1, hi) if b < ts else (lo, mid)
    return lo


def morning(day):
    """Taker-side USDC and trade count for 00:00 to 12:00 UTC on one day."""
    start = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())
    a, b = block_at(start), block_at(start + 12 * 3600)
    usd = trades = 0
    exchanges = {e.lower() for e in EXCHANGES}
    while a < b:
        res = query({"from_block": a, "to_block": b,
                     "logs": [{"address": EXCHANGES, "topics": [[ORDERS_MATCHED]]}],
                     "field_selection": {"log": ["address", "topic0", "data"]}})
        for batch in res["data"]:
            for log in batch.get("logs", []):
                if log["topic0"].lower() != ORDERS_MATCHED or log["address"].lower() not in exchanges:
                    continue
                d = log["data"][2:]
                side, maker_amt, taker_amt = int(d[0:64], 16), int(d[128:192], 16), int(d[192:256], 16)
                usd += (maker_amt if side == 0 else taker_amt) / 1e6  # side 0 = buy, USDC has 6 decimals
                trades += 1
        a = res["next_block"]
    return usd, trades


day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(dt.timezone.utc).date()
days = [day - dt.timedelta(days=i) for i in range(6, -1, -1)]
print("Reading 7 mornings in parallel, this takes a few minutes...", flush=True)
with ThreadPoolExecutor(max_workers=7) as pool:
    results = list(pool.map(morning, days))
rows = [(d, usd, n) for d, (usd, n) in zip(days, results)]
for d, usd, n in rows:
    print(f"{d:%a %d %b}  ${usd/1e6:6.1f}M  {n:>8,} trades  ${usd/max(n,1):5.0f} avg trade")

prev = rows[:-1]
avg_usd = sum(r[1] for r in prev) / len(prev)
avg_n = sum(r[2] for r in prev) / len(prev)
_, usd, n = rows[-1]
print(f"\n{day}: ${usd/1e6:.1f}M by midday UTC, {usd/avg_usd-1:+.0%} vs the 6-day average, "
      f"trades {n/avg_n-1:+.0%}, average trade ${sum(r[1] for r in prev)/sum(r[2] for r in prev):.0f} -> ${usd/n:.0f}")
