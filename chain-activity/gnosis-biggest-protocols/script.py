# The busiest protocols on Gnosis Chain over the last 30 days, with Envio HyperSync.
# For each protocol it reads every event its core contracts emitted, counts the transactions that touched them
# and the wallets that sent those transactions. Gnosis Pay card payments come from its Spend events.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
# Optional: python script.py <from_block> <to_block> to rerun an exact window.
import collections
import json
import os
import sys
import time
import urllib.request

URL = "https://gnosis.hypersync.xyz"
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

# Core contracts per protocol, each taken from the protocol's own docs or repos (see README)
PROTOCOLS = {
    "Lido Data Bus": ["0x37De961D6bb5865867aDd416be07189D2Dd960e6"],
    "HOPR": ["0x75Ce59332721E3aE3064cb9652BCE35FFCE3f8E6",   # channels, piz-palu-prod
             "0x860f50B24Ba6A862736c5045747323e03aa52Aa4"],  # channels, jura-prod
    "Balancer": ["0xBA12222222228d8Ba445958a75a0704d566BF2C8",   # Vault V2
                 "0xbA1333333333a1BA1108E8412f11850A5C319bA9"],  # Vault V3
    "Spark": ["0x2Dae5307c5E3FD1CF5A72Cb6F698f915860607e0"],     # SparkLend Pool
    "Aave": ["0xb50201558B00496A145fE76f7424749556E326D8"],      # Aave V3 Pool
    "Circles": ["0xc12C1E50ABB450d6205Ea2C3Fa861b3B834d13e8"],   # Circles v2 Hub
    "Gnosis Pay": ["0x5f07734E2B9C4dE6f9C32253d485741800da3F8a",  # spend module
                   "0xcFF260bfbc199dC82717494299b1AcADe25F549b"],  # older spend module
    "Olas": ["0x735FAAb1c4Ec41128c367AFb5c3baC73509f70bB"],      # Mech Marketplace
    "CoW Protocol": ["0x9008D19f58AAbD9eD0D60971565AA8510560ab41"],  # GPv2Settlement
}
SPEND = "0xca8fbb9bda99848f447971eae62ad0ad2bc7caf9afcc0d8e4e8ffcf7e06bc28f"  # Spend(asset, account, receiver, amount)


def post(path, body=None):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + path)


def block_time(n):
    res = post("/query", {"from_block": n, "to_block": n + 1, "include_all_blocks": True,
                          "field_selection": {"block": ["timestamp"]}})
    return int(res["data"][0]["blocks"][0]["timestamp"], 16)


# 1. The window, the last 30 days up to the latest block (or the blocks you pass in)
if len(sys.argv) == 3:
    start, end = int(sys.argv[1]), int(sys.argv[2])
else:
    end = post("/height")["height"]
    target = block_time(end - 1) - 30 * 86400
    lo, hi = end - 700_000, end - 1  # Gnosis makes a block every 5 seconds, so 30 days is about 518K blocks
    while lo < hi:
        mid = (lo + hi) // 2
        if block_time(mid) < target:
            lo = mid + 1
        else:
            hi = mid
    start = lo

# 2. Every event from every core contract, joined to the transaction that emitted it
owner = {a.lower(): p for p, addrs in PROTOCOLS.items() for a in addrs}
txs, wallets = collections.defaultdict(set), collections.defaultdict(set)
spends, cardholders = 0, set()
body = {"from_block": start, "to_block": end, "logs": [{"address": list(owner)}],
        "field_selection": {"log": ["address", "transaction_hash", "topic0", "data"], "transaction": ["hash", "from"]}}
while True:
    res = post("/query", body)
    for batch in res["data"]:
        sender = {t["hash"]: t["from"].lower() for t in batch.get("transactions") or []}
        for log in batch.get("logs") or []:
            protocol = owner.get(log["address"].lower())
            if not protocol:
                continue
            txs[protocol].add(log["transaction_hash"])
            wallets[protocol].add(sender.get(log["transaction_hash"]))
            if protocol == "Gnosis Pay" and log.get("topic0") == SPEND:
                spends += 1
                cardholders.add(log["data"][2 + 64 + 24:2 + 128])  # second word of the data is the card account's Safe
    print(f"  read to block {res['next_block']:,}", file=sys.stderr)
    if res["next_block"] >= end:
        break
    body["from_block"] = res["next_block"]

# 3. Rank
print(f"Busiest protocols on Gnosis Chain, blocks {start:,} to {end:,} (30 days)")
print(f"  {'':14}{'transactions':>14}{'wallets sending':>18}")
for protocol in sorted(PROTOCOLS, key=lambda p: -len(txs[p])):
    print(f"  {protocol:14}{len(txs[protocol]):>14,}{len(wallets[protocol] - {None}):>18,}")
print(f"Gnosis Pay: {spends:,} card payments from {len(cardholders):,} card accounts (its transactions are sent by Gnosis Pay, not the cardholder)")
