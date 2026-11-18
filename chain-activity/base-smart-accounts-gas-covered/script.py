"""Count smart accounts on Base (or any EVM chain) and how many had gas covered by a paymaster.

Reads every ERC-4337 UserOperationEvent from EntryPoint 0.6, 0.7 and 0.8 with HyperSync.
Standard library only. Needs ENVIO_API_TOKEN.

  CHAIN=base DAYS=7 python3 script.py
"""
import json, os, sys, time, bisect, collections
import urllib.request as u

TOKEN = os.environ["ENVIO_API_TOKEN"]
CHAIN = os.environ.get("CHAIN", "base")
DAYS = int(os.environ.get("DAYS", "7"))
URL = f"https://{CHAIN}.hypersync.xyz"
ENTRYPOINTS = [
    "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789",  # EntryPoint 0.6
    "0x0000000071727de22e5e9d8baf0edac6f37da032",  # EntryPoint 0.7
    "0x4337084d9e255ff0702461cf8895ce9e3b5ff108",  # EntryPoint 0.8
]
# UserOperationEvent(bytes32 indexed userOpHash, address indexed sender, address indexed paymaster, ...)
TOPIC0 = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
ZERO = "0x" + "0" * 64


def call(path, body=None):
    for i in range(8):
        try:
            data = json.dumps(body).encode() if body is not None else None
            req = u.Request(URL + path, data, {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
            return json.load(u.urlopen(req, timeout=300))
        except Exception as e:
            print("retry", e, file=sys.stderr)
            time.sleep(3 * (i + 1))
    sys.exit("HyperSync request failed")


def timestamp(block):
    d = call("/query", {"from_block": block, "to_block": block + 1, "include_all_blocks": True,
                        "field_selection": {"block": ["number", "timestamp"]}})
    return int(d["data"][0]["blocks"][0]["timestamp"], 16)


def block_at(t, lo, hi):
    """First block at or after timestamp t."""
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if timestamp(mid) < t:
            lo = mid
        else:
            hi = mid
    return hi


head = call("/height")["height"] - 1000  # stay clear of the tip
now = timestamp(head)
bounds = [block_at(now - 86400 * k, 0, head) for k in range(DAYS, 0, -1)] + [head + 1]

rows = []
cur = bounds[0]
while cur <= head:
    d = call("/query", {"from_block": cur, "to_block": head + 1,
                        "logs": [{"address": ENTRYPOINTS, "topics": [[TOPIC0]]}],
                        "field_selection": {"log": ["block_number", "address", "topic2", "topic3"]}})
    for batch in d["data"]:
        for l in batch["logs"]:
            rows.append((l["block_number"], l["topic2"][-40:], l["topic3"] != ZERO))
    if d["next_block"] <= cur:
        break
    cur = d["next_block"]
    print(f"block {cur:,}  ops {len(rows):,}", file=sys.stderr)

rows.sort()
blocks = [r[0] for r in rows]
accounts = collections.defaultdict(lambda: [0, 0])  # ops, sponsored ops
for _, sender, sponsored in rows:
    accounts[sender][0] += 1
    accounts[sender][1] += sponsored

print(f"\nUser operations      {len(rows):>12,}")
print(f"Smart accounts       {len(accounts):>12,}")
print(f"With a gas-covered op{sum(1 for a in accounts.values() if a[1]):>12,}")
print(f"Every op gas-covered {sum(1 for a in accounts.values() if a[0] == a[1]):>12,}")
print("\nday   accounts   with a gas-covered op")
for i in range(DAYS):
    seg = rows[bisect.bisect_left(blocks, bounds[i]):bisect.bisect_left(blocks, bounds[i + 1])]
    print(f"{i + 1:<4}  {len({r[1] for r in seg}):>8,}   {len({r[1] for r in seg if r[2]}):>8,}")
