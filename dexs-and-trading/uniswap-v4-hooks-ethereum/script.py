# Uniswap v4 pools on Ethereum: every pool created on the PoolManager, and how many use a hook.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import datetime
import json
import os
import sys
import time
import urllib.request

URL = "https://eth.hypersync.xyz/query"
# PoolManager on Ethereum, from Uniswap's v4 deployments: https://docs.uniswap.org/contracts/v4/deployments
POOL_MANAGER = "0x000000000004444c5dc75cb358380d2e3de08a90"
INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
START_BLOCK = 21688329  # PoolManager deployment
NO_HOOK = "0x" + "0" * 40
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def query(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


body = {
    "from_block": START_BLOCK,
    "logs": [{"address": [POOL_MANAGER], "topics": [[INITIALIZE]]}],
    "field_selection": {"block": ["number", "timestamp"],
                        "log": ["block_number", "address", "topic0", "data"]},
}
pools = collections.Counter()
hooked = collections.Counter()
hooks = collections.Counter()
while True:
    res = query(body)
    for batch in res["data"]:
        ts = {b["number"]: (int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"])
              for b in batch.get("blocks") or []}
        for log in batch.get("logs") or []:
            if log["address"].lower() != POOL_MANAGER or log["topic0"] != INITIALIZE:
                continue
            # Initialize data: currency0 and currency1 are indexed, then fee, tickSpacing, hooks, sqrtPriceX96, tick
            hook = "0x" + log["data"][2:][64 * 2 + 24:64 * 3].lower()
            month = datetime.datetime.fromtimestamp(ts[log["block_number"]], datetime.timezone.utc).strftime("%Y-%m")
            pools[month] += 1
            if hook != NO_HOOK:
                hooked[month] += 1
                hooks[hook] += 1
    if res["next_block"] >= res["archive_height"]:
        break
    body["from_block"] = res["next_block"]

total, with_hook = sum(pools.values()), sum(hooked.values())
print(f"{total:,} v4 pools on Ethereum, {with_hook:,} with a hook ({100 * with_hook / total:.1f}%), "
      f"{len(hooks):,} different hook contracts\n")
for month in sorted(pools):
    print(f"{month}  {pools[month]:>7,} pools  {hooked[month]:>7,} with a hook")
print("\nMost used hooks:")
for hook, n in hooks.most_common(5):
    print(f"  {hook}  {n:,} pools")
