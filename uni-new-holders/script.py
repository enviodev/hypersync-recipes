"""
Count how many addresses touch an ERC-20 token for the first time each day,
from the token's whole history, using Envio HyperSync.

Usage:
    export ENVIO_API_TOKEN=...          # free token: https://docs.envio.dev/docs/HyperSync/api-tokens
    python3 new_addresses.py                                   # UNI on Ethereum
    python3 new_addresses.py 0xTokenAddress 12345678           # any ERC-20, optional start block

An address counts on the UTC day it first sends or receives the token.
Writes new_addresses.csv (day, new_addresses, transfers) and prints the busiest days.
"""
import csv, datetime, json, os, sys, time, urllib.error, urllib.request
from collections import Counter

HYPERSYNC = "https://eth.hypersync.xyz/query"   # Ethereum mainnet
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKEN = (sys.argv[1] if len(sys.argv) > 1 else "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984").lower()  # UNI
START_BLOCK = int(sys.argv[2]) if len(sys.argv) > 2 else 10_861_674  # UNI deployment block
ZERO = "0" * 40


def query(body):
    req = urllib.request.Request(HYPERSYNC, json.dumps(body).encode(), {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['ENVIO_API_TOKEN']}",
    })
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            time.sleep(5 * (attempt + 1))  # rate limited or busy, wait and retry
    raise RuntimeError("HyperSync kept refusing the request")


seen, new_per_day, transfers_per_day = set(), Counter(), Counter()
block = START_BLOCK
while True:
    res = query({
        "from_block": block,
        "logs": [{"address": [TOKEN], "topics": [[TRANSFER]]}],
        "field_selection": {
            "block": ["number", "timestamp"],
            "log": ["block_number", "log_index", "address", "topic0", "topic1", "topic2"],
        },
    })
    timestamps = {}
    for batch in res["data"]:
        for b in batch.get("blocks", []):
            t = b["timestamp"]
            timestamps[b["number"]] = int(t, 16) if isinstance(t, str) else t
    logs = sorted((l for batch in res["data"] for l in batch.get("logs", [])),
                  key=lambda l: (l["block_number"], l["log_index"]))
    for log in logs:
        if log["address"].lower() != TOKEN or log["topic0"] != TRANSFER:
            continue
        day = datetime.datetime.fromtimestamp(timestamps[log["block_number"]], datetime.timezone.utc).date().isoformat()
        transfers_per_day[day] += 1
        for address in (log["topic1"][-40:], log["topic2"][-40:]):
            if address != ZERO and address not in seen:
                seen.add(address)
                new_per_day[day] += 1
    next_block = res["next_block"]
    if next_block <= block or next_block > res.get("archive_height", next_block):
        break
    block = next_block
    print(f"\rblock {block:,}  addresses {len(seen):,}", end="", flush=True)

with open("new_addresses.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["day", "new_addresses", "transfers"])
    for day in sorted(transfers_per_day):
        w.writerow([day, new_per_day[day], transfers_per_day[day]])

print(f"\n\n{len(seen):,} addresses in total. Busiest days for new addresses:")
for day, n in new_per_day.most_common(5):
    print(f"  {day}  {n:,}")
