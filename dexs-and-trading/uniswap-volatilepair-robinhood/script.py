# Uniswap's VolatilePair hook on Robinhood Chain: every swap in its ETH/USDG pool, with Envio HyperSync.
# Prints swaps, USDG volume and the LP fee the hook charged on each side of the market.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import datetime
import json
import os
import statistics
import sys
import time
import urllib.request

URL = "https://robinhood.hypersync.xyz"
# From https://developers.uniswap.org/docs/protocols/v4/deployments and
# https://developers.uniswap.org/docs/protocols/uniswap-labs-hooks/volatile-pair/deployments (Robinhood Chain, 4663)
POOL_MANAGER = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
POOL_ID = "0xa791e5169faf703c0b63fd9552c33ec1128a773a00f5dc33a640da62a022cd35"  # ETH / USDG
INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
TO_BLOCK = int(sys.argv[1]) if len(sys.argv) > 1 else None  # optional, to rerun a past snapshot exactly


def query(body):
    req = urllib.request.Request(URL + "/query", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def logs(topics, from_block):
    body = {"from_block": from_block, "logs": [{"address": [POOL_MANAGER], "topics": topics}],
            "field_selection": {"block": ["number", "timestamp"],
                                "log": ["block_number", "address", "topic0", "topic1", "data"]}}
    if TO_BLOCK:
        body["to_block"] = TO_BLOCK + 1
    while True:
        res = query(body)
        for batch in res["data"]:
            ts = {b["number"]: (int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"])
                  for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                if log["address"].lower() == POOL_MANAGER and log["topic0"].lower() == topics[0][0] \
                        and log["topic1"].lower() == POOL_ID:
                    yield log, ts.get(log["block_number"])
        end = TO_BLOCK + 1 if TO_BLOCK else res["archive_height"]
        if res["next_block"] >= end:
            return
        body["from_block"] = res["next_block"]


def signed(word):
    v = int(word, 16)
    return v - (1 << 256) if v >> 255 else v


init_block = next(logs([[INITIALIZE], [POOL_ID]], 0))[0]["block_number"]
swaps = []
for log, ts in logs([[SWAP], [POOL_ID]], init_block):
    d = log["data"][2:]
    amount0, amount1, fee = signed(d[0:64]), signed(d[64:128]), int(d[320:384], 16)
    # Swap amounts are from the swapper's side: a negative amount is what the swapper paid in.
    side = "buy ETH" if amount1 < 0 else "sell ETH"
    swaps.append(dict(block=log["block_number"], ts=ts, usdg=abs(amount1) / 1e6, fee=fee, side=side))

fmt = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%d %b %H:%M UTC")
print(f"VolatilePair ETH/USDG pool on Robinhood Chain, {fmt(swaps[0]['ts'])} to {fmt(swaps[-1]['ts'])}")
print(f"Swaps         {len(swaps):,}")
print(f"USDG volume   ${sum(s['usdg'] for s in swaps):,.0f}")
by_day = collections.Counter(datetime.datetime.fromtimestamp(s["ts"], datetime.timezone.utc).date() for s in swaps)
for day, n in sorted(by_day.items()):
    print(f"  {day}  {n:,} swaps")
# The hook sets the LP fee per swap. Fees are in hundredths of a basis point (100 = 0.01%).
for side in ("buy ETH", "sell ETH"):
    fees = [s["fee"] for s in swaps if s["side"] == side]
    print(f"{side:9} {len(fees):,} swaps, median LP fee {statistics.median(fees) / 100:.2f} bp")
if len(sys.argv) > 2:  # optional: write hourly swap counts for charting
    hourly = collections.Counter(datetime.datetime.fromtimestamp(s["ts"], datetime.timezone.utc).strftime("%Y-%m-%d %H") for s in swaps)
    json.dump(sorted(hourly.items()), open(sys.argv[2], "w"))
