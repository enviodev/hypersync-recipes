"""Every strategy shipped on 1inch Aqua, on all 15 chains it runs on.

Aqua is 1inch's shared liquidity layer. A liquidity provider "ships" a strategy, and one token
balance can back many strategies. The Aqua registry has the same address on every chain and emits
one Shipped event per strategy. This script reads every Shipped event with Envio HyperSync and
prints strategies, distinct LP wallets and the share by chain.

Usage:  ENVIO_API_TOKEN=... python3 script.py
        CHAIN=base python3 script.py      (one chain only)
"""
import collections, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (free at https://envio.dev/app/api-tokens)")
# Aqua registry, the same address on every chain (1inch/aqua deployments.md)
AQUA = "0x1111113ccf1426a8e30e2bff5e005d929bf6a90a"
# topic0 of Shipped(address maker, address app, bytes32 strategyHash, bytes strategy)
SHIPPED = "0xdc3622e06fb145651f567d421c9ef261d71d43e3778b761907bc0d70d42e52b0"
CHAINS = ["eth", "base", "optimism", "polygon", "arbitrum", "avalanche", "bsc", "gnosis",
          "linea", "sonic", "unichain", "zksync", "robinhood", "arc", "monad"]  # HyperSync subdomains
if os.environ.get("CHAIN"): CHAINS = [os.environ["CHAIN"]]

def post(url, body):
    for i in range(8):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(),
                {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception as e:
            print("retry", e, file=sys.stderr); time.sleep(2 * (i + 1))
    sys.exit("query failed")

def read_chain(sub):
    url = f"https://{sub}.hypersync.xyz/query"
    height = json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://{sub}.hypersync.xyz/height", headers={"Authorization": "Bearer " + TOKEN}), timeout=30))["height"]
    body = {"from_block": 0, "logs": [{"address": [AQUA], "topics": [[SHIPPED]]}],
            "field_selection": {"log": ["block_number", "data"]}}
    makers = collections.Counter()
    while True:
        r = post(url, body)
        for batch in r.get("data") or []:
            for log in batch.get("logs") or []:
                makers["0x" + log["data"][2 + 24:2 + 64]] += 1  # first word of data is the maker address
        nxt = r.get("next_block")
        if not nxt or nxt >= r.get("archive_height", height) or nxt <= body["from_block"]: break
        body["from_block"] = nxt
    return sub, makers

with ThreadPoolExecutor(6) as ex:
    results = dict(ex.map(read_chain, CHAINS))

total = sum(sum(m.values()) for m in results.values())
all_makers = collections.Counter()
for m in results.values(): all_makers.update(m)
print(f"1inch Aqua, all chains: {total:,} strategies shipped by {len(all_makers):,} different wallets")
print(f"Wallets that shipped 10 or more: {sum(1 for c in all_makers.values() if c >= 10):,}")
print(f"Chains with at least one strategy: {sum(1 for m in results.values() if m)} of {len(results)}\n")
print(f"{'chain':12s} {'strategies':>11s} {'share':>7s} {'wallets':>8s}")
for sub, m in sorted(results.items(), key=lambda kv: -sum(kv[1].values())):
    n = sum(m.values()); print(f"{sub:12s} {n:11,d} {n / total * 100:6.1f}% {len(m):8,d}")
