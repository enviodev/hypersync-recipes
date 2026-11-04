"""Polymarket trading volume by hour, read straight from Polygon with Envio HyperSync.

Reproduces the numbers in Envio's US election night post: taker-side USDC traded on
Polymarket's exchange contracts from 1pm to 3am US Eastern time on a given night,
hour by hour, compared with the same Eastern hours on each of the seven nights before.

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
from zoneinfo import ZoneInfo
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


ET = ZoneInfo("America/New_York")
HOURS = 14  # 1pm to 3am Eastern


def night(day):
    """Taker-side USDC per hour and trade count from 1pm to 3am Eastern on one night."""
    start = int(dt.datetime(day.year, day.month, day.day, 13, tzinfo=ET).timestamp())
    a, b = block_at(start), block_at(start + HOURS * 3600)
    hourly = [0.0] * HOURS
    trades = 0
    exchanges = {e.lower() for e in EXCHANGES}
    while a < b:
        res = query({"from_block": a, "to_block": b,
                     "logs": [{"address": EXCHANGES, "topics": [[ORDERS_MATCHED]]}],
                     "field_selection": {"block": ["number", "timestamp"],
                                         "log": ["block_number", "address", "topic0", "data"]}})
        for batch in res["data"]:
            ts = {bl["number"]: (int(bl["timestamp"], 16) if isinstance(bl["timestamp"], str) else bl["timestamp"])
                  for bl in batch.get("blocks", [])}
            for log in batch.get("logs", []):
                if log["topic0"].lower() != ORDERS_MATCHED or log["address"].lower() not in exchanges:
                    continue
                d = log["data"][2:]
                side, maker_amt, taker_amt = int(d[0:64], 16), int(d[128:192], 16), int(d[192:256], 16)
                h = (ts[log["block_number"]] - start) // 3600
                if 0 <= h < HOURS:
                    hourly[h] += (maker_amt if side == 0 else taker_amt) / 1e6  # side 0 = buy, USDC has 6 decimals
                    trades += 1
        a = res["next_block"]
    return hourly, trades


day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(ET).date() - dt.timedelta(days=1)
days = [day - dt.timedelta(days=i) for i in range(7, -1, -1)]
print("Reading 8 nights in parallel, this takes a few minutes...", flush=True)
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(night, days))
for d, (hourly, n) in zip(days, results):
    print(f"{d:%a %d %b}  ${sum(hourly)/1e6:6.1f}M  {n:>8,} trades  ${sum(hourly)/max(n,1):5.0f} avg trade")

prev = results[:-1]
hourly, n = results[-1]
avg_night = sum(sum(h) for h, _ in prev) / len(prev)
avg_hour = [sum(h[i] for h, _ in prev) / len(prev) for i in range(HOURS)]
peak = max(range(HOURS), key=lambda i: hourly[i])
label = (dt.datetime(2000, 1, 1, 13) + dt.timedelta(hours=peak)).strftime("%-I%p").lower()
print(f"\n{day}: ${sum(hourly)/1e6:.1f}M from 1pm to 3am ET, {sum(hourly)/avg_night-1:+.0%} vs the 7-night average of ${avg_night/1e6:.1f}M")
print(f"Busiest hour {label} ET, ${hourly[peak]/1e6:.2f}M, {hourly[peak]/avg_hour[peak]:.1f}x a normal {label}")
print(f"Average trade ${sum(sum(h) for h, _ in prev)/sum(c for _, c in prev):.0f} -> ${sum(hourly)/n:.0f}")
