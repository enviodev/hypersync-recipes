# Monad's biggest apps over the last 30 days, with Envio HyperSync.
# Reads every transaction sent to a contract in the Monad Foundation's protocol registry
# (github.com/monad-crypto/protocols) and ranks protocols by unique sending wallets and by transactions.
# Oracles and Monad's canonical contracts (staking precompile, WMON, EntryPoint, Multicall, Permit2) are left out.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import csv
import io
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HYPERSYNC = "https://monad.hypersync.xyz"
REGISTRY = "https://raw.githubusercontent.com/monad-crypto/protocols/main/protocols-mainnet.csv"
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
TOP = 10

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def get(url, body=None):
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    if url.startswith(HYPERSYNC):
        headers["Authorization"] = "Bearer " + TOKEN  # the token only ever goes to HyperSync
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    for attempt in range(10):
        try:
            raw = urllib.request.urlopen(req, timeout=300).read()
            return json.loads(raw) if url.startswith(HYPERSYNC) else raw.decode()
        except Exception:
            time.sleep(3 * (attempt + 1))  # also covers HyperSync's per-minute rate limit
    sys.exit("Request kept failing: " + url)


def block_time(n):
    res = get(HYPERSYNC + "/query", {"from_block": n, "to_block": n + 1, "include_all_blocks": True,
                                     "field_selection": {"block": ["timestamp"]}})
    return int(res["data"][0]["blocks"][0]["timestamp"], 16)


# 1. Contract addresses per protocol, from the Monad Foundation's registry
protocol_of = {}
for row in csv.DictReader(io.StringIO(get(REGISTRY))):
    if row["name"] == "Canonical Contracts" or row["csubtype"] == "Oracle":
        continue
    protocol_of[row["address"].lower()] = row["name"]

# 2. The block range covering the last DAYS days
end = get(HYPERSYNC + "/height")["height"] - 1
target = block_time(end) - DAYS * 86400
lo, hi = 1, end
while lo < hi:
    mid = (lo + hi) // 2
    lo, hi = (mid + 1, hi) if block_time(mid) < target else (lo, mid)
start = lo

# 3. Every transaction sent to a registry contract, read in parallel block ranges
txs, senders = collections.Counter(), collections.defaultdict(set)
lock = threading.Lock()


def scan(first):
    last = min(first + 20000, end + 1)
    body = {"from_block": first, "to_block": last, "transactions": [{"to": list(protocol_of)}],
            "field_selection": {"transaction": ["to", "from"]}}
    t, s = collections.Counter(), collections.defaultdict(set)
    while True:
        res = get(HYPERSYNC + "/query", body)
        for batch in res["data"]:
            for tx in batch.get("transactions") or []:
                name = protocol_of.get((tx.get("to") or "").lower())
                if name:
                    t[name] += 1
                    s[name].add(tx["from"].lower())
        if res["next_block"] >= last:
            break
        body["from_block"] = res["next_block"]
    with lock:
        txs.update(t)
        for name, wallets in s.items():
            senders[name] |= wallets


with ThreadPoolExecutor(16) as pool:
    list(pool.map(scan, range(start, end + 1, 20000)))

# 4. Rankings
print(f"Monad, blocks {start} to {end} (last {DAYS} days), {len(protocol_of)} registry contracts")
print(f"\nTop {TOP} apps by unique wallets sending transactions")
for i, (name, wallets) in enumerate(sorted(senders.items(), key=lambda kv: -len(kv[1]))[:TOP], 1):
    print(f"  {i:2}. {name:16} {len(wallets):>7,} wallets  {txs[name]:>12,} txs")
print(f"\nTop {TOP} apps by transactions")
for i, (name, n) in enumerate(txs.most_common(TOP), 1):
    print(f"  {i:2}. {name:16} {n:>12,} txs  {len(senders[name]):>7,} wallets")
