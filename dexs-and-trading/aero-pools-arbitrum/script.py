"""The biggest Aero pools on Arbitrum, read straight from the chain with Envio HyperSync.

Finds every pool created by Aero's CL and volatile pool factories on Arbitrum, reads
every swap in them since launch, prices each swap in dollars, and reads what each pool
holds right now. Prints the pools ranked by swap volume and by liquidity.

Run:
    export ENVIO_API_TOKEN=...   # free token: https://envio.dev/app/api-tokens
    python script.py               # up to the latest block
    python script.py 521465669     # up to a fixed block, to rerun the post's numbers
"""
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

URL = "https://arbitrum.hypersync.xyz/query"
RPC = "https://arb1.arbitrum.io/rpc"
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN first")

# Aero factories on Arbitrum, from github.com/dromos-labs/metadex-slipstream-public
# (deployment-addresses/cl-arbitrum.json and pools-arbitrum.json)
CL_FACTORY = "0x88a60ee77392577c355c0acb2a8d476d5a4ec03a"
VOLATILE_FACTORY = "0x8e6a9fcd1d638cc760ffba397605fe3355de76d2"
STABLE_FACTORY = "0x78589e876edcebdce72ee3436ab3c9ad3a7cef2d"
FIRST_BLOCK = 516786000  # just before the factories were deployed

CL_POOL_CREATED = "0xab0d57f0df537bb25e80245ef7748fa62353808c54d6e528a9dd20887aed9ac2"
V2_POOL_CREATED = "0xebbbe9dc3a19d2f959ac76ac0372b4983cdfb945f5d6aef4873c36fabb2ba8aa"
CL_SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
V2_SWAP = "0xb3e2773606abfd36b5bd91394b3a54d1398336c65005baf7bf7a05efeffaf75b"

# Dollar stablecoins on Arbitrum, valued at $1
STABLES = {
    "0xaf88d065e77c8cc2239327c5edb3a432268e5831",  # USDC
    "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8",  # USDC.e
    "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9",  # USDT0
    "0x004b506865409877c9fa29bfb1eba929984b9bbc",  # USDG
    "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1",  # DAI
    "0x7dff72693f6a4149b17e7c6314655f6a9f7c8b33",  # GHO
    "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34",  # USDe
    "0x0a1a1a107e45b7ced86833863f482bc5f4ed82ef",  # USDai
}
WETH = "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
WBTC = "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f"
BASES = [WETH, WBTC]  # priced from their deepest Aero stablecoin pool


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


END_BLOCK = int(sys.argv[1]) if len(sys.argv) > 1 else None


def stream(body):
    """Yield every page of a HyperSync query up to END_BLOCK or the chain head."""
    if END_BLOCK:
        body["to_block"] = END_BLOCK + 1
    while True:
        res = query(body)
        yield res
        body["from_block"] = res["next_block"]
        if res["next_block"] >= body.get("to_block", res.get("archive_height", 0)):
            return


def rpc(method, params):
    req = urllib.request.Request(RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                                                  "params": params}).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "envio-recipe"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["result"]
        except Exception:
            time.sleep(1 + attempt)
    sys.exit("RPC request kept failing")


def call(to, data, block="latest"):
    return rpc("eth_call", [{"to": to, "data": data}, block])


def symbol(token):
    raw = bytes.fromhex(call(token, "0x95d89b41")[2:])
    if len(raw) >= 96:
        return raw[64:64 + int.from_bytes(raw[32:64], "big")].decode()
    return raw.rstrip(b"\0").decode()


def signed(word):
    v = int(word, 16)
    return v - (1 << 256) if v >= 1 << 255 else v


def main():
    # 1. Every pool the Aero factories have created
    pools = {}
    for res in stream({"from_block": FIRST_BLOCK, "logs": [
            {"address": [CL_FACTORY], "topics": [[CL_POOL_CREATED]]},
            {"address": [VOLATILE_FACTORY, STABLE_FACTORY], "topics": [[V2_POOL_CREATED]]}],
            "field_selection": {"log": ["topic0", "topic1", "topic2", "data"]}}):
        for page in res["data"]:
            for log in page.get("logs", []):
                pool = "0x" + log["data"][26:66]
                pools[pool] = {"t0": "0x" + log["topic1"][-40:], "t1": "0x" + log["topic2"][-40:],
                               "cl": log["topic0"] == CL_POOL_CREATED}
    tokens = {t for p in pools.values() for t in (p["t0"], p["t1"])}
    dec = {t: int(call(t, "0x313ce567"), 16) for t in tokens}
    sym = {t: symbol(t) for t in tokens}

    # 2. Every swap in those pools, in order, priced in dollars
    price = {t: 1.0 for t in STABLES}
    vol = defaultdict(float)
    swaps = defaultdict(int)
    unpriced = 0
    traders = set()
    first_ts = last_ts = None
    for res in stream({"from_block": FIRST_BLOCK,
                       "logs": [{"address": list(pools), "topics": [[CL_SWAP, V2_SWAP]]}],
                       "field_selection": {"log": ["address", "topic0", "data", "block_number"],
                                           "transaction": ["from"],
                                           "block": ["number", "timestamp"]}}):
        for page in res["data"]:
            for b in page.get("blocks", []):
                ts = int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                first_ts = first_ts or ts
                last_ts = ts
            for tx in page.get("transactions", []):
                traders.add(tx["from"].lower())
            for log in page.get("logs", []):
                pool = log["address"].lower()
                p = pools[pool]
                t0, t1 = p["t0"], p["t1"]
                w = [log["data"][2 + 64 * i: 66 + 64 * i] for i in range(len(log["data"]) // 64)]
                if p["cl"]:
                    a0 = abs(signed(w[0])) / 10 ** dec[t0]
                    a1 = abs(signed(w[1])) / 10 ** dec[t1]
                    # token1 per token0 at the pool's new price
                    ratio = (int(w[2], 16) / 2 ** 96) ** 2 * 10 ** (dec[t0] - dec[t1])
                    # learn prices from pools quoted against a stablecoin, WETH or WBTC
                    for known, other, conv in ((t1, t0, ratio), (t0, t1, 1 / ratio if ratio else 0)):
                        if known in price and other not in STABLES and conv:
                            if known in STABLES or known in BASES or other not in BASES:
                                if other in BASES and known not in STABLES:
                                    continue
                                price[other] = price[known] * conv
                else:
                    a0 = (int(w[0], 16) + int(w[2], 16)) / 10 ** dec[t0]
                    a1 = (int(w[1], 16) + int(w[3], 16)) / 10 ** dec[t1]
                # value the swap on its most reliable priced side
                for t, a in sorted(((t0, a0), (t1, a1)),
                                   key=lambda x: (x[0] not in STABLES, x[0] not in BASES)):
                    if t in price:
                        vol[pool] += a * price[t]
                        break
                else:
                    unpriced += 1
                swaps[pool] += 1

    # 3. What each pool holds now, at the same block for every pool
    head = hex(END_BLOCK) if END_BLOCK else rpc("eth_blockNumber", [])
    tvl = {}
    for pool, p in pools.items():
        tvl[pool] = 0.0
        for t in (p["t0"], p["t1"]):
            bal = int(call(t, "0x70a08231" + pool[2:].rjust(64, "0"), head), 16) / 10 ** dec[t]
            tvl[pool] += bal * price.get(t, 0)

    name = {pool: f"{sym[p['t0']]}/{sym[p['t1']]}{'' if p['cl'] else ' (volatile)'}"
            for pool, p in pools.items()}
    total_vol, total_tvl = sum(vol.values()), sum(tvl.values())
    days = (last_ts - first_ts) / 86400
    print(f"Aero on Arbitrum: {len(pools)} pools, {sum(1 for s in swaps.values() if s)} with swaps, "
          f"over {days:.1f} days")
    print(f"Swap volume ${total_vol / 1e6:,.1f}M across {sum(swaps.values()):,} swaps "
          f"from {len(traders):,} wallets ({unpriced} swaps unpriced)")
    print(f"Liquidity ${total_tvl / 1e6:,.2f}M at block {int(head, 16)}\n")
    print("Top pools by swap volume")
    for pool in sorted(vol, key=vol.get, reverse=True)[:10]:
        print(f"  {name[pool]:<22} ${vol[pool] / 1e6:8,.1f}M  {vol[pool] / total_vol:6.1%}  "
              f"{swaps[pool]:>7,} swaps  {pool}")
    print("\nTop pools by liquidity")
    for pool in sorted(tvl, key=tvl.get, reverse=True)[:10]:
        print(f"  {name[pool]:<22} ${tvl[pool] / 1e6:8,.2f}M  {tvl[pool] / total_tvl:6.1%}  {pool}")
    top7 = sorted(vol, key=vol.get, reverse=True)[:7]
    rest = [pl for pl in pools if pl not in top7]
    print(f"\nThe other {len(rest)} pools: ${sum(vol[pl] for pl in rest) / 1e6:,.1f}M volume, "
          f"${sum(tvl[pl] for pl in rest) / 1e6:,.2f}M liquidity")
    print(f"Volume is {total_vol / total_tvl:.0f}x liquidity")
    top5 = sum(sorted(vol.values(), reverse=True)[:5])
    print(f"Top 5 pools: {top5 / total_vol:.1%} of volume")
    usdg = [pl for pl, p in pools.items() if "USDG" in (sym[p["t0"]], sym[p["t1"]])]
    print(f"USDG pools: {len(usdg)} of {len(pools)}, "
          f"{sum(vol[pl] for pl in usdg) / total_vol:.1%} of volume, "
          f"{sum(tvl[pl] for pl in usdg) / total_tvl:.1%} of liquidity")
    print("\nPrices used for liquidity: " + ", ".join(
        f"{sym[t]} ${price[t]:,.2f}" for t in (WETH, WBTC) if t in price))


if __name__ == "__main__":
    main()
