# Uniswap on Robinhood Chain: every swap on v2, v3 and v4, with Envio HyperSync.
# Prints swaps per Uniswap version, the total, when the total passed 1M, 10M, 100M and so on,
# and how many Robinhood stock tokens have traded on Uniswap.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
#
#   python script.py                      every swap since launch (slow: hundreds of millions of logs)
#   python script.py 2026-11-01 2026-11-02 swaps between two UTC dates
import datetime
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = "https://robinhood.hypersync.xyz"
# Uniswap deployments on Robinhood Chain (4663), from https://developers.uniswap.org/docs/protocols
POOL_MANAGER = "0x8366a39cc670b4001a1121b8f6a443a643e40951"  # v4
V3_FACTORY = "0x1f7d7550b1b028f7571e69a784071f0205fd2efa"
V2_FACTORY = "0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f"
V4_INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
V4_SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
V3_POOL_CREATED = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
V3_SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
V2_PAIR_CREATED = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
V2_SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
# Robinhood stock tokens, from the API that https://docs.robinhood.com/chain/stock-tokens points to
STOCK_API = "https://api.robinhood.com/rhj/assets"
MILESTONES = [1e6, 1e7, 1e8, 2e8, 3e8, 4e8]

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(body):
    req = urllib.request.Request(URL + "/query", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(12):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def height():
    req = urllib.request.Request(URL + "/height", headers={"Authorization": "Bearer " + TOKEN})
    return json.load(urllib.request.urlopen(req, timeout=60))["height"]


def logs(address, topic0, start, end, fields, with_time=False):
    """Yield (log, timestamp) for one event, paging with next_block. Address and topic0 are checked again here."""
    sel = {"topics": [[topic0]]}
    if address:
        sel["address"] = [address]
    body = {"from_block": start, "to_block": end, "logs": [sel], "field_selection": {"log": list(fields)}}
    if with_time:
        body["field_selection"]["block"] = ["number", "timestamp"]
    while body["from_block"] < end:
        res = post(body)
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                  for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                if log["topic0"].lower() != topic0 or (address and log["address"].lower() != address):
                    continue
                yield log, ts.get(log.get("block_number"))
        if res["next_block"] <= body["from_block"]:
            break
        body["from_block"] = res["next_block"]


def chunks(start, end, n):
    step = (end - start) // n + 1
    return [(start + i * step, min(end, start + (i + 1) * step)) for i in range(n) if start + i * step < end]


def parallel(fn, start, end, n=32):
    with ThreadPoolExecutor(16) as ex:
        return list(ex.map(lambda r: fn(*r), chunks(start, end, n)))


def addr(word):
    return ("0x" + word[-40:]).lower()


def block_at(ts, top):
    """First block at or after a UTC timestamp, by binary search on block timestamps."""
    lo, hi = 0, top
    while hi - lo > 1:
        mid = (lo + hi) // 2
        res = post({"from_block": mid, "to_block": mid + 1, "include_all_blocks": True,
                    "field_selection": {"block": ["number", "timestamp"]}})
        t = res["data"][0]["blocks"][0]["timestamp"]
        t = int(t, 16) if isinstance(t, str) else t
        lo, hi = (mid, hi) if t < ts else (lo, mid)
    return hi


top = height()
if len(sys.argv) > 2:
    utc = lambda d: int(datetime.datetime.fromisoformat(d).replace(tzinfo=datetime.timezone.utc).timestamp())
    start, end = block_at(utc(sys.argv[1]), top), block_at(utc(sys.argv[2]), top)
else:
    start, end = 0, top + 1
print(f"Robinhood Chain blocks {start:,} to {end:,}", flush=True)

# 1. Every official pool, with its two tokens. v2 and v3 swaps only count if the pool came from the official factory.
def v4_pools(a, b):
    return [(l["topic1"].lower(), addr(l["topic2"]), addr(l["topic3"]))
            for l, _ in logs(POOL_MANAGER, V4_INITIALIZE, a, b, ("address", "topic0", "topic1", "topic2", "topic3"))]
def v3_pools(a, b):
    return [(("0x" + l["data"][2 + 64 + 24:2 + 128]).lower(), addr(l["topic1"]), addr(l["topic2"]))
            for l, _ in logs(V3_FACTORY, V3_POOL_CREATED, a, b, ("address", "topic0", "topic1", "topic2", "data"))]
def v2_pools(a, b):
    return [(("0x" + l["data"][2 + 24:2 + 64]).lower(), addr(l["topic1"]), addr(l["topic2"]))
            for l, _ in logs(V2_FACTORY, V2_PAIR_CREATED, a, b, ("address", "topic0", "topic1", "topic2", "data"))]
pools = {}
for name, fn in (("v4", v4_pools), ("v3", v3_pools), ("v2", v2_pools)):
    pools[name] = {k: (t0, t1) for part in parallel(fn, 0, end) for k, t0, t1 in part}
    print(f"{name} pools {len(pools[name]):,}", flush=True)

# 2. Every swap: count per version and per hour, and note which pools traded.
def swaps(version, topic0, address):
    def run(a, b):
        hours, traded = {}, set()
        for l, t in logs(address, topic0, a, b, ("address", "topic0", "topic1", "block_number"), with_time=True):
            key = l["topic1"].lower() if version == "v4" else l["address"].lower()
            if key not in pools[version]:
                continue
            hours[t // 3600] = hours.get(t // 3600, 0) + 1
            traded.add(key)
        return hours, traded
    return parallel(run, start, end, 256)

hours, traded, by_version = {}, {}, {}
for version, topic0, address in (("v4", V4_SWAP, POOL_MANAGER), ("v3", V3_SWAP, None), ("v2", V2_SWAP, None)):
    traded[version] = set()
    total = 0
    for h, tr in swaps(version, topic0, address):
        for k, v in h.items():
            hours[k] = hours.get(k, 0) + v
            total += v
        traded[version] |= tr
    by_version[version] = total
    print(f"{version} swaps {total:,}", flush=True)

total = sum(by_version.values())
print(f"\nTotal Uniswap swaps {total:,}")

if start == 0:
    first_active = int(datetime.datetime(2026, 7, 1, tzinfo=datetime.timezone.utc).timestamp())
    running, todo = 0, list(MILESTONES)
    for h in sorted(hours):
        running += hours[h]
        while todo and running >= todo[0]:
            when = datetime.datetime.fromtimestamp(h * 3600, datetime.timezone.utc)
            days = (h * 3600 - first_active) / 86400
            print(f"  passed {todo.pop(0) / 1e6:,.0f}M swaps {when:%d %b %Y %H:00} UTC, {days:.1f} days after 1st July")

req = urllib.request.Request(STOCK_API, headers={"User-Agent": "Mozilla/5.0"})
stocks = {d["contractAddress"].lower() for a in json.load(urllib.request.urlopen(req, timeout=60))["assets"]
          for d in a.get("deployments", []) if d.get("chainId") == 4663}
seen = set()
for version in traded:
    for key in traded[version]:
        seen |= {t for t in pools[version][key] if t in stocks}
print(f"Robinhood stock tokens traded on Uniswap: {len(seen)} of {len(stocks)}")
