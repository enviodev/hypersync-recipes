# Coinbase tokenized stocks on Aero (Base), with Envio HyperSync.
# Finds every Aero pool on Base that holds a Coinbase tokenized stock, reads every swap in those
# pools over the last N days, and prints USDC-paired volume per stock and how much of it traded
# while US stock markets were closed.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import Counter

URL = "https://base.hypersync.xyz"
POOL_CREATED_V2 = "0x2128d88d14c80cb081c1252a5acff7a264671bf199ce226b53788fb26065005e"
POOL_CREATED_CL = "0xab0d57f0df537bb25e80245ef7748fa62353808c54d6e528a9dd20887aed9ac2"
SWAP_V2 = "0xb3e2773606abfd36b5bd91394b3a54d1398336c65005baf7bf7a05efeffaf75b"
SWAP_CL = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
# Pool factories on Base:
#   Aerodrome classic: github.com/aerodrome-finance/contracts
#   Aerodrome Slipstream (3 deployments): github.com/aerodrome-finance/slipstream
#   Aero CL: github.com/dromos-labs/metadex-slipstream-public, deployment-addresses/cl-base.json
FACTORIES = {
    "0x420dd381b31aef6683db6b902084cb0ffece40da": POOL_CREATED_V2,
    "0x5e7bb104d84c7cb9b682aac2f3d509f5f406809a": POOL_CREATED_CL,
    "0xade65c38cd4849adba595a4323a8c7ddfe89716a": POOL_CREATED_CL,
    "0xf8f2eb4940cfe7d13603dddd87f123820fc061ef": POOL_CREATED_CL,
    "0x9cb220581b91b0c83223012fe69688b92ad07a76": POOL_CREATED_CL,
}
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"  # USDC on Base, 6 decimals
STOCKS_API = "https://api.coinbase.com/v1/tokenized-stocks"  # docs.base.org/sdks/tokenized-stocks

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 7
# Optional end time in UTC, e.g. 2026-11-04T09:40:09, to rerun a past window exactly.
END = (int(datetime.datetime.fromisoformat(sys.argv[2]).replace(tzinfo=datetime.timezone.utc).timestamp())
       if len(sys.argv) > 2 else None)


def get(url, body=None):
    headers = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json", "User-Agent": "curl/8"}
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def block_time(number):
    res = get(URL + "/query", {"from_block": number, "to_block": number + 1, "include_all_blocks": True,
                               "field_selection": {"block": ["number", "timestamp"]}})
    t = res["data"][0]["blocks"][0]["timestamp"]
    return int(t, 16) if isinstance(t, str) else t


def first_block_after(ts, lo, hi):
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if block_time(mid) < ts else (lo, mid)
    return hi


def logs(body, check):
    while True:
        res = get(URL + "/query", body)
        for batch in res["data"]:
            times = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                     for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                if check(log):
                    yield log, times.get(log.get("block_number"))
        if res["next_block"] >= body.get("to_block", res["archive_height"]) or res["next_block"] >= res["archive_height"]:
            return
        body["from_block"] = res["next_block"]


def market_open(ts):
    # US regular hours, 9:30am to 4pm ET on weekdays. Uses EDT before 1st Nov 2026 and EST after.
    offset = 4 if ts < 1793512800 else 5
    et = datetime.datetime.fromtimestamp(ts - offset * 3600, datetime.timezone.utc)
    minutes = et.hour * 60 + et.minute
    return et.weekday() < 5 and 570 <= minutes < 960


# 1. Coinbase tokenized stocks
stocks, page = {}, ""
while True:
    res = get(STOCKS_API + "?page_size=500" + ("&page_token=" + page if page else ""))
    for s in next(v for v in res.values() if isinstance(v, list)):
        stocks[s["contract_address"].lower()] = s["symbol"]
    page = res.get("next_page_token")
    if not page:
        break

# 2. Every Aero pool that holds one
pools = {}
for factory, topic in FACTORIES.items():
    body = {"from_block": 0, "logs": [{"address": [factory], "topics": [[topic]]}],
            "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data"]}}
    for log, _ in logs(body, lambda l, f=factory, t=topic: l["address"].lower() == f and l["topic0"] == t):
        a, b = "0x" + log["topic1"][-40:], "0x" + log["topic2"][-40:]
        if a in stocks or b in stocks:
            pools["0x" + log["data"][26:66]] = ("cl" if topic == POOL_CREATED_CL else "v2", a, b)

# 3. Swaps in the window
height = get(URL + "/height")["height"]
end = END or block_time(height - 1)
start = end - DAYS * 86400
b0 = first_block_after(start, height - 50 * 43200 * DAYS // 7 - 1, height - 1)
b1 = first_block_after(end + 1, b0, height)
volume, closed = Counter(), Counter()
body = {"from_block": b0, "to_block": b1, "logs": [{"address": sorted(pools), "topics": [[SWAP_V2, SWAP_CL]]}],
        "field_selection": {"block": ["number", "timestamp"], "log": ["address", "topic0", "data", "block_number"]}}
for log, ts in logs(body, lambda l: l["address"].lower() in pools):
    kind, a, b = pools[log["address"].lower()]
    if log["topic0"] != (SWAP_CL if kind == "cl" else SWAP_V2) or USDC not in (a, b):
        continue
    words = [int(log["data"][2 + i * 64:2 + (i + 1) * 64], 16) for i in range(4)]
    i = 0 if a == USDC else 1
    if kind == "cl":
        raw = words[i] - (1 << 256) if words[i] >> 255 else words[i]
        usd = abs(raw) / 1e6
    else:
        usd = (words[i] + words[i + 2]) / 1e6
    sym = stocks[b if a == USDC else a]
    volume[sym] += usd
    if not market_open(ts):
        closed[sym] += usd

total, shut = sum(volume.values()), sum(closed.values())
fmt = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%d %b %H:%M UTC")
print(f"Coinbase tokenized stocks on Aero (Base), {fmt(start)} to {fmt(end)}")
print(f"Pools holding a stock: {len(pools):,}")
print(f"USDC-paired volume: ${total / 1e6:,.1f}M, {100 * shut / total:.1f}% while US markets were closed")
for sym, v in volume.most_common(8):
    print(f"  {sym:8} ${v / 1e6:7,.1f}M  {100 * closed[sym] / v:5.1f}% closed")
