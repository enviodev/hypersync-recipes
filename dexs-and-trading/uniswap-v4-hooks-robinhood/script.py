# Uniswap v4 hooks on Robinhood: every pool created on the v4 PoolManager, which hook it uses,
# and every swap, with Envio HyperSync.
# Prints pools with and without a hook, how many different hook contracts there are,
# the top hooks by pools and by swaps, and pools and swaps per month.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
#
#   python script.py                       everything up to the latest block
#   python script.py 110095000             stop at a fixed block, to rerun the exact numbers
#   python script.py 110095000 --pools-only  pools and hooks only, skipping the swaps (much faster)
#   python script.py --ethereum 26378070   the same pool and hook counts for v4 on Ethereum (no swaps)
import collections
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# PoolManagers from Uniswap's v4 deployments page: https://developers.uniswap.org/docs/protocols/v4/deployments
ETHEREUM = "--ethereum" in sys.argv
if ETHEREUM:
    NAME, URL, POOL_MANAGER = "Ethereum (chain 1)", "https://eth.hypersync.xyz", "0x000000000004444c5dc75cb358380d2e3de08a90"
else:
    NAME, URL, POOL_MANAGER = "Robinhood (chain 4663)", "https://robinhood.hypersync.xyz", "0x8366a39cc670b4001a1121b8f6a443a643e40951"
# Initialize(bytes32 indexed id, address indexed currency0, address indexed currency1,
#            uint24 fee, int24 tickSpacing, address hooks, uint160 sqrtPriceX96, int24 tick)
INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
# Swap(bytes32 indexed id, address indexed sender, int128 amount0, int128 amount1,
#      uint160 sqrtPriceX96, uint128 liquidity, int24 tick, uint24 fee)
SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
NO_HOOK = "0x" + "0" * 40

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(URL + path, data=data,
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(30):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except urllib.error.HTTPError as e:
            # 429 means the token's per-minute budget is used up; wait for the window to reset
            wait = int(e.headers.get("x-ratelimit-reset") or 5) + 1 if e.code == 429 else 3
            time.sleep(wait)
        except Exception:
            time.sleep(3)
    sys.exit("HyperSync request kept failing")


def logs(topic0, start, end, fields, with_time=True):
    """Yield (log, unix time or None) for one PoolManager event, paging with next_block.
    HyperSync filters on address and topic0 server-side."""
    body = {"from_block": start, "to_block": end,
            "logs": [{"address": [POOL_MANAGER], "topics": [[topic0]]}],
            "field_selection": {"log": ["block_number"] + fields}}
    if with_time:
        body["field_selection"]["block"] = ["number", "timestamp"]
    while body["from_block"] < end:
        res = post("/query", body)
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                  for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                yield log, ts.get(log["block_number"])
        if res["next_block"] <= body["from_block"]:
            break
        body["from_block"] = res["next_block"]


def block_at(t, top):
    """First block at or after a unix time, by binary search on block timestamps."""
    lo, hi = 0, top
    while hi - lo > 1:
        mid = (lo + hi) // 2
        res = post("/query", {"from_block": mid, "to_block": mid + 1, "include_all_blocks": True,
                              "field_selection": {"block": ["number", "timestamp"]}})
        bt = res["data"][0]["blocks"][0]["timestamp"]
        bt = int(bt, 16) if isinstance(bt, str) else bt
        lo, hi = (mid, hi) if bt < t else (lo, mid)
    return hi


def parallel(fn, start, end, n):
    step = (end - start) // n + 1
    ranges = [(start + i * step, min(end, start + (i + 1) * step)) for i in range(n) if start + i * step < end]
    with ThreadPoolExecutor(8) as ex:
        return list(ex.map(lambda r: fn(*r), ranges))


def month(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m")


args = [a for a in sys.argv[1:] if a.isdigit()]
end = int(args[0]) if args else post("/height")["height"] + 1
print(f"Uniswap v4 on {NAME}, blocks 0 to {end:,}\n", flush=True)

# 1. Every pool: its id, its hook and when it was created.
def read_pools(a, b):
    out = []
    for log, t in logs(INITIALIZE, a, b, ["topic1", "data"]):
        hook = ("0x" + log["data"][2 + 64 * 2 + 24:2 + 64 * 3]).lower()  # third data word
        out.append((log["topic1"].lower(), hook, t))
    return out

pools = {pid: (hook, t) for part in parallel(read_pools, 0, end, 32) for pid, hook, t in part}
hook_pools = collections.Counter(hook for hook, _ in pools.values() if hook != NO_HOOK)
print(f"Pools created         {len(pools):>12,}")
print(f"  with a hook         {sum(hook_pools.values()):>12,}  ({100 * sum(hook_pools.values()) / len(pools):.1f}%)")
print(f"Different hooks       {len(hook_pools):>12,}")
print(f"  used by 2+ pools    {sum(1 for n in hook_pools.values() if n >= 2):>12,}")
print(f"  used by 10+ pools   {sum(1 for n in hook_pools.values() if n >= 10):>12,}", flush=True)
if ETHEREUM or "--pools-only" in sys.argv:
    sys.exit()

# 2. Every swap: count per pool, and per month using the first block of each UTC month.
first = min(t for _, t in pools.values())
months, d = [], datetime.datetime.fromtimestamp(first, datetime.timezone.utc).replace(day=1, hour=0, minute=0, second=0)
while d.timestamp() < time.time():
    months.append(d)
    d = (d + datetime.timedelta(days=32)).replace(day=1)
edges = [(m.strftime("%Y-%m"), block_at(int(m.timestamp()), end)) for m in months]

def read_swaps(a, b):
    per_pool = collections.Counter()
    for log, _ in logs(SWAP, a, b, ["topic1"], with_time=False):
        per_pool[log["topic1"].lower(), max(m for m, blk in edges if blk <= log["block_number"])] += 1
    print(".", end="", file=sys.stderr, flush=True)
    return per_pool

swaps_pool, swaps_month = collections.Counter(), collections.Counter()
for part in parallel(read_swaps, 0, end, 400):
    for (pid, m), n in part.items():
        swaps_pool[pid] += n
        swaps_month[(m, pools.get(pid, (NO_HOOK,))[0] != NO_HOOK)] += n
print(file=sys.stderr)

hooked = {pid for pid, (hook, _) in pools.items() if hook != NO_HOOK}
hook_swaps = collections.Counter()
for pid, n in swaps_pool.items():
    if pid in hooked:
        hook_swaps[pools[pid][0]] += n
total_swaps = sum(swaps_pool.values())
hooked_swaps = sum(hook_swaps.values())
unknown = sum(n for pid, n in swaps_pool.items() if pid not in pools)

print(f"Swaps                 {total_swaps:>12,}")
print(f"  in pools with hook  {hooked_swaps:>12,}  ({100 * hooked_swaps / total_swaps:.1f}%)")
if unknown:
    print(f"  in pools not found  {unknown:>12,}")

print("\nTop hooks by pools created:")
for hook, n in hook_pools.most_common(10):
    print(f"  {hook}  {n:>9,} pools  {hook_swaps[hook]:>11,} swaps")
print("\nTop hooks by swaps:")
for hook, n in hook_swaps.most_common(10):
    print(f"  {hook}  {n:>11,} swaps  {100 * n / total_swaps:5.1f}% of all v4 swaps  {hook_pools[hook]:>9,} pools")

print("\nPer month (UTC):          pools   with hook        swaps   in hooked pools")
pm, pmh = collections.Counter(), collections.Counter()
for pid, (hook, t) in pools.items():
    pm[month(t)] += 1
    if hook != NO_HOOK:
        pmh[month(t)] += 1
for m in sorted(set(pm) | {k[0] for k in swaps_month}):
    s = swaps_month[(m, True)] + swaps_month[(m, False)]
    print(f"  {m}  {pm[m]:>12,}  {pmh[m]:>10,}  {s:>11,}  {swaps_month[(m, True)]:>11,}")

if "--json" in sys.argv:
    json.dump({"end_block": end,
               "pools_per_day": sorted(collections.Counter(
                   (datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d"), h != NO_HOOK)
                   for h, t in pools.values()).items()),
               "hook_pools": hook_pools.most_common(), "hook_swaps": hook_swaps.most_common()},
              open("hooks.json", "w"), default=list)
