# Ethereum's busiest NFT collections: count every ERC-721 Transfer over the last 24 hours (7,200 blocks) with Envio
# HyperSync, then read each top collection's name from a standard RPC. Python 3.9+ standard library only.
# Set ENVIO_API_TOKEN first. Usage: python3 script.py            the last 7,200 blocks
#                                   python3 script.py FROM TO    a fixed block range
import collections
import json
import os
import sys
import time
import urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

HYPERSYNC = "https://eth.hypersync.xyz"
RPC = os.environ.get("RPC_URL", "https://ethereum-rpc.publicnode.com")  # HyperRPC has no eth_call, so names come from any standard RPC
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64


def post(url, body, headers=None):
    req = urllib.request.Request(url, json.dumps(body).encode(), headers or {"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:  # rate limits and timeouts: wait and try again
            time.sleep(2 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def call(to, data):
    r = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]})
    return r.get("result")


def text(hex_result):
    if not hex_result or hex_result == "0x":
        return None
    raw = bytes.fromhex(hex_result[2:])
    try:
        return raw[64:64 + int.from_bytes(raw[32:64], "big")].decode()
    except Exception:
        return raw.rstrip(b"\0").decode(errors="ignore") or None


# An ERC-721 Transfer has the token id indexed, so it has a fourth topic. An ERC-20 Transfer does not.
if len(sys.argv) == 3:
    start, height = int(sys.argv[1]), int(sys.argv[2])
else:
    height = json.load(urllib.request.urlopen(HYPERSYNC + "/height", timeout=30))["height"]
    start = height - 7200  # 7,200 Ethereum blocks is about 24 hours
transfers, mints = collections.Counter(), collections.Counter()
block = start
while block <= height:
    r = post(HYPERSYNC + "/query", {
        "from_block": block, "to_block": height + 1,
        "logs": [{"topics": [[TRANSFER]]}],
        "field_selection": {"log": ["address", "topic1", "topic3"]}},
        {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for page in r["data"]:
        for log in page["logs"]:
            if log.get("topic3"):
                addr = log["address"].lower()
                transfers[addr] += 1
                if log["topic1"] == ZERO:
                    mints[addr] += 1
    if r["next_block"] <= block:
        break
    block = r["next_block"]

print(f"Ethereum NFT transfers, blocks {start:,} to {height:,} ({height - start:,} blocks, about {(height - start) * 12 // 3600} hours)")
print(f"{sum(transfers.values()):,} transfers across {len(transfers):,} collections\n")
for rank, (addr, count) in enumerate(transfers.most_common(10), 1):
    name, symbol = text(call(addr, "0x06fdde03")), text(call(addr, "0x95d89b41"))
    print(f"{rank:>2}  {count:>7,} transfers  {mints[addr]:>6,} mints  {name} ({symbol})  {addr}")

total = sum(transfers.values())
ranked = transfers.most_common()
print(f"\nThe five biggest DeFi collections above (ranks 1, 2, 3, 5, 6) made up "
      f"{sum(ranked[i][1] for i in (0, 1, 2, 4, 5)):,} of {total:,} transfers, "
      f"{100 * sum(ranked[i][1] for i in (0, 1, 2, 4, 5)) / total:.1f}%")
