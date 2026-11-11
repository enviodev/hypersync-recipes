# Every Safe created per month, chain by chain, with Envio HyperSync.
# Reads the ProxyCreation event from Safe's canonical proxy factories (1.3.0, 1.4.1, 1.5.0) as listed in
# Safe's own deployments repo (github.com/safe-global/safe-deployments), keeps proxies that point at an
# official Safe singleton (L1 or L2 build), and counts them by calendar month (UTC) and by chain.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

CHAINS = {  # chain id: name (HyperSync endpoint is https://<id>.hypersync.xyz)
    1: "Ethereum", 8453: "Base", 10: "Optimism", 137: "Polygon", 42161: "Arbitrum",
    56: "BNB Chain", 100: "Gnosis", 43114: "Avalanche", 130: "Unichain", 80094: "Berachain",
    534352: "Scroll", 42220: "Celo", 59144: "Linea", 57073: "Ink",
}
DEPLOYMENTS = "https://raw.githubusercontent.com/safe-global/safe-deployments/main/src/assets/"
FACTORY_FILES = ["v1.3.0/proxy_factory.json", "v1.4.1/safe_proxy_factory.json", "v1.5.0/safe_proxy_factory.json"]
SINGLETON_FILES = ["v1.3.0/gnosis_safe.json", "v1.3.0/gnosis_safe_l2.json", "v1.4.1/safe.json",
                   "v1.4.1/safe_l2.json", "v1.5.0/safe.json", "v1.5.0/safe_l2.json"]
# keccak256("ProxyCreation(address,address)"), the same in every factory version
PROXY_CREATION = "0x4f51faf6c4561ff95f067657e43439f0f856d97c04d9ec9070a6199ad418e235"

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def get(url, body=None):
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if ".hypersync.xyz" in url:
        headers["Authorization"] = "Bearer " + TOKEN  # the token only ever goes to HyperSync
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    for attempt in range(10):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception:
            time.sleep(3 * (attempt + 1))  # also covers HyperSync's per-minute rate limit
    sys.exit("Request kept failing: " + url)


def addresses(files):
    out = set()
    for f in files:
        for d in get(DEPLOYMENTS + f)["deployments"].values():
            if d["address"]:
                out.add(d["address"].lower())
    return out


FACTORIES = sorted(addresses(FACTORY_FILES))
SINGLETONS = addresses(SINGLETON_FILES)


def scan(job):
    chain, first, last = job
    url = "https://%d.hypersync.xyz/query" % chain
    body = {"from_block": first, "to_block": last,
            "logs": [{"address": FACTORIES, "topics": [[PROXY_CREATION]]}],
            "field_selection": {"log": ["block_number", "topic1", "data"], "block": ["number", "timestamp"]}}
    months, proxies = collections.Counter(), set()
    while True:
        res = get(url, body)
        times = {}
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                times[int(b["number"], 16) if isinstance(b["number"], str) else b["number"]] = int(b["timestamp"], 16)
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                data = log["data"][2:]
                if log.get("topic1"):  # 1.4.1 and later: proxy is indexed, singleton in data
                    proxy, singleton = log["topic1"][-40:], data[24:64]
                else:  # 1.3.0: both in data
                    proxy, singleton = data[24:64], data[88:128]
                if "0x" + singleton not in SINGLETONS or proxy in proxies:
                    continue
                proxies.add(proxy)
                month = datetime.fromtimestamp(times[log["block_number"]], timezone.utc).strftime("%Y-%m")
                months[month] += 1
        nxt = res["next_block"]
        if nxt >= last:
            return chain, months
        body["from_block"] = nxt


jobs = []
for chain in CHAINS:
    height = get("https://%d.hypersync.xyz/height" % chain)["height"]
    step = height // 16 + 1
    jobs += [(chain, s, min(s + step, height + 1)) for s in range(0, height + 1, step)]

per_chain = collections.defaultdict(collections.Counter)
with ThreadPoolExecutor(16) as pool:
    for chain, months in pool.map(scan, jobs):
        per_chain[chain].update(months)

total = collections.Counter()
for c in per_chain.values():
    total.update(c)
now = datetime.now(timezone.utc)
this_month = now.strftime("%Y-%m")

print("Safes created from Safe's 1.3.0, 1.4.1 and 1.5.0 factories on %d chains, as of %s UTC\n"
      % (len(CHAINS), now.strftime("%d %b %Y %H:%M")))
print("By chain (all time)")
for chain, c in sorted(per_chain.items(), key=lambda kv: -sum(kv[1].values())):
    print("  %-10s %12s" % (CHAINS[chain], format(sum(c.values()), ",")))
print("  %-10s %12s\n" % ("Total", format(sum(total.values()), ",")))

print("By month, last 24 months (%s is month to date)" % this_month)
for m in sorted(total)[-24:]:
    print("  %s %12s" % (m, format(total[m], ",")))
full = {m: v for m, v in total.items() if m != this_month}
best = max(full, key=full.get)
print("\nRecord full month: %s with %s Safes" % (best, format(full[best], ",")))
for y in sorted({m[:4] for m in total})[-3:]:
    print("Created in %s: %s" % (y, format(sum(v for m, v in total.items() if m.startswith(y)), ",")))

year = now.strftime("%Y")
print("\nCreated in %s by chain" % year)
for chain, c in sorted(per_chain.items(), key=lambda kv: -sum(v for m, v in kv[1].items() if m.startswith(year))):
    print("  %-10s %12s" % (CHAINS[chain], format(sum(v for m, v in c.items() if m.startswith(year)), ",")))

json.dump({"chains": {CHAINS[c]: dict(sorted(v.items())) for c, v in per_chain.items()}, "as_of": now.isoformat()},
          open("safes_by_month.json", "w"), indent=1)
