"""Aero's swap volume on Robinhood and on Ethereum, day by day, with Envio HyperSync.

Finds every pool created by Aero's factories on each chain, reads every swap in
them since Aero launched there, prices each swap in dollars and prints volume,
swaps and wallets per UTC day for both chains side by side.

Run:
    export ENVIO_API_TOKEN=...   # free token: https://envio.dev/app/api-tokens
    python script.py               # every full UTC day so far
    python script.py 2026-11-15    # stop after this UTC day, to rerun the post's numbers
"""
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN first")
UTC = datetime.timezone.utc
LAST_DAY = sys.argv[1] if len(sys.argv) > 1 else (
    datetime.datetime.now(UTC) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# Aero factories, from github.com/dromos-labs/metadex-slipstream-public
# (deployment-addresses/cl-<chain>.json and pools-<chain>.json).
# The volatile and stable pool factories have the same address on both chains.
VOLATILE_FACTORY = "0x8e6a9fcd1d638cc760ffba397605fe3355de76d2"
STABLE_FACTORY = "0x78589e876edcebdce72ee3436ab3c9ad3a7cef2d"
CHAINS = {
    "Robinhood": {
        "hypersync": "https://robinhood.hypersync.xyz",
        "rpc": "https://rpc.mainnet.chain.robinhood.com",
        "cl_factory": "0xc63d7338c178e805c544b8f897066bd3bbcbe136",
        "first_block": 94_000_000,  # just before the factories were deployed
        "stables": {"0x5fc5360d0400a0fd4f2af552add042d716f1d168"},  # USDG
        "bases": ["0x0bd7d308f8e1639fab988df18a8011f41eacad73",   # WETH
                  "0xcec185eb182c47d1ba1efc84e6959e18cd620be4"],  # cbBTC
    },
    "Ethereum": {
        "hypersync": "https://eth.hypersync.xyz",
        "rpc": "https://ethereum-rpc.publicnode.com",
        "cl_factory": "0xf4fd2e6c5b60c5b365cd1b96dd6245e6d60414c2",
        "first_block": 26_230_000,
        "stables": {
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
            "0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
            "0xf939e0a03fb07f59a73314e73794be0e57ac1b4e",  # crvUSD
            "0xcacd6fd266af91b8aed52accc382b4e165586e29",  # frxUSD
            "0x4c9edd5852cd905f086c759e8383e09bff1e68b3",  # USDe
            "0xdc035d45d973e3ec169d2276ddab16f1e407384f",  # USDS
        },
        "bases": ["0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",   # WETH
                  "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",   # WBTC
                  "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"],  # cbBTC
    },
}
CL_POOL_CREATED = "0xab0d57f0df537bb25e80245ef7748fa62353808c54d6e528a9dd20887aed9ac2"
V2_POOL_CREATED = "0xebbbe9dc3a19d2f959ac76ac0372b4983cdfb945f5d6aef4873c36fabb2ba8aa"
CL_SWAP = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
V2_SWAP = "0xb3e2773606abfd36b5bd91394b3a54d1398336c65005baf7bf7a05efeffaf75b"


def post(url, body=None):
    for attempt in range(30):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode() if body else None, {
                "Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}",
                "User-Agent": "envio-recipe"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(min(30, 3 * (attempt + 1)))  # HyperSync rate-limits, so back off
    sys.exit("request kept failing")


def stream(hs, body):
    head = post(hs + "/height")["height"]
    body["to_block"] = head
    while True:
        res = post(hs + "/query", body)
        yield res
        if res["next_block"] >= head:
            return
        body["from_block"] = res["next_block"]


def decimals(rpc, token):
    res = post(rpc, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                     "params": [{"to": token, "data": "0x313ce567"}, "latest"]})
    return int(res["result"], 16)


def signed(word):
    v = int(word, 16)
    return v - (1 << 256) if v >= 1 << 255 else v


def chain_days(name, c):
    hs, stables, bases = c["hypersync"], c["stables"], c["bases"]
    factories = {c["cl_factory"], VOLATILE_FACTORY, STABLE_FACTORY}
    # 1. Every pool the Aero factories have created
    pools = {}
    for res in stream(hs, {"from_block": c["first_block"], "logs": [
            {"address": [c["cl_factory"]], "topics": [[CL_POOL_CREATED]]},
            {"address": [VOLATILE_FACTORY, STABLE_FACTORY], "topics": [[V2_POOL_CREATED]]}],
            "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data"]}}):
        for page in res["data"]:
            for log in page.get("logs") or []:
                if log["address"].lower() in factories:  # default join, so check what came back
                    pools["0x" + log["data"][26:66]] = {
                        "t0": "0x" + log["topic1"][-40:], "t1": "0x" + log["topic2"][-40:],
                        "cl": log["topic0"] == CL_POOL_CREATED}
    dec = {t: decimals(c["rpc"], t) for t in {t for p in pools.values() for t in (p["t0"], p["t1"])}}

    # 2. Every swap in those pools, in order, priced in dollars
    price = {t: 1.0 for t in stables}
    days = defaultdict(lambda: {"usd": 0.0, "swaps": 0, "wallets": set(), "unpriced": 0})
    for res in stream(hs, {"from_block": c["first_block"],
                           "logs": [{"address": list(pools), "topics": [[CL_SWAP, V2_SWAP]]}],
                           "field_selection": {"log": ["address", "topic0", "data", "block_number",
                                                       "transaction_hash"],
                                               "transaction": ["hash", "from"],
                                               "block": ["number", "timestamp"]}}):
        for page in res["data"]:
            ts = {}
            for b in page.get("blocks") or []:
                t = b["timestamp"]
                ts[b["number"]] = int(t, 16) if isinstance(t, str) else t
            sender = {tx["hash"]: tx["from"].lower() for tx in page.get("transactions") or []}
            for log in page.get("logs") or []:
                pool = log["address"].lower()
                if pool not in pools or log["topic0"] not in (CL_SWAP, V2_SWAP):
                    continue
                p = pools[pool]
                t0, t1 = p["t0"], p["t1"]
                w = [log["data"][2 + 64 * i: 66 + 64 * i] for i in range(len(log["data"]) // 64)]
                if p["cl"]:
                    a0 = abs(signed(w[0])) / 10 ** dec[t0]
                    a1 = abs(signed(w[1])) / 10 ** dec[t1]
                    # token1 per token0 at the pool's new price
                    ratio = (int(w[2], 16) / 2 ** 96) ** 2 * 10 ** (dec[t0] - dec[t1])
                    # learn prices: WETH and BTC from stablecoin pools, everything else from
                    # its pool against a stablecoin, WETH or BTC
                    for known, other, conv in ((t1, t0, ratio), (t0, t1, 1 / ratio if ratio else 0)):
                        if known in price and other not in stables and conv:
                            if other in bases and known not in stables:
                                continue
                            if known in stables or known in bases:
                                price[other] = price[known] * conv
                else:
                    a0 = (int(w[0], 16) + int(w[2], 16)) / 10 ** dec[t0]
                    a1 = (int(w[1], 16) + int(w[3], 16)) / 10 ** dec[t1]
                d = days[datetime.datetime.fromtimestamp(ts[log["block_number"]], UTC).strftime("%Y-%m-%d")]
                # value the swap on one side: a stablecoin if there is one, then WETH or BTC
                for t, a in sorted(((t0, a0), (t1, a1)),
                                   key=lambda x: (x[0] not in stables, x[0] not in bases)):
                    if t in price:
                        d["usd"] += a * price[t]
                        break
                else:
                    d["unpriced"] += 1
                d["swaps"] += 1
                d["wallets"].add(sender.get(log["transaction_hash"]))
    return len(pools), {k: v for k, v in days.items() if k <= LAST_DAY}


def main():
    out = {}
    for name, c in CHAINS.items():
        n, days = chain_days(name, c)
        out[name] = days
        swaps = sum(d["swaps"] for d in days.values())
        wallets = set().union(*(d["wallets"] for d in days.values()))
        print(f"Aero on {name}: {n} pools, first swap {min(days)}, "
              f"${sum(d['usd'] for d in days.values()) / 1e6:,.1f}M across {swaps:,} swaps "
              f"from {len(wallets):,} wallets ({sum(d['unpriced'] for d in days.values())} unpriced)")
    both = sorted(set(out["Robinhood"]) & set(out["Ethereum"]))
    print("\nday          Robinhood     Ethereum   Robinhood as % of Ethereum")
    for day in both:
        r, e = out["Robinhood"][day]["usd"], out["Ethereum"][day]["usd"]
        print(f"{day}  ${r / 1e6:8.1f}M  ${e / 1e6:8.1f}M  {100 * r / e:6.1f}%")
    last7 = both[-7:]
    for name in CHAINS:
        usd = sum(out[name][d]["usd"] for d in last7)
        swaps = sum(out[name][d]["swaps"] for d in last7)
        wallets = set().union(*(out[name][d]["wallets"] for d in last7))
        print(f"\n{name}, {last7[0]} to {last7[-1]}: ${usd / 1e6:,.1f}M, {swaps:,} swaps, "
              f"{len(wallets):,} wallets, ${usd / swaps:,.0f} a swap")
    if os.environ.get("DUMP"):
        json.dump({n: {d: {"usd": v["usd"], "swaps": v["swaps"], "wallets": len(v["wallets"])}
                       for d, v in days.items()} for n, days in out.items()},
                  open(os.environ["DUMP"], "w"))


main()
