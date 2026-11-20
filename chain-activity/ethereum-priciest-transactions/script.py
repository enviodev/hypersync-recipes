# Ethereum's priciest transactions: rank every transaction in 24 hours by the fee it paid, with Envio HyperSync.
# Fee = gas used x effective gas price. Also shows how far each gas price sat above the block's base fee.
# Python 3.9+ standard library only. Set ENVIO_API_TOKEN first.
# Usage: python3 script.py            the last 7,200 blocks, about 24 hours
#        python3 script.py FROM TO    a fixed block range
import heapq
import json
import os
import sys
import time
import urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

URL = "https://eth.hypersync.xyz"
HEADERS = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}


def num(v):
    return v if isinstance(v, int) else int(v, 16)


def post(body):
    req = urllib.request.Request(URL + "/query", json.dumps(body).encode(), HEADERS)
    for attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:  # rate limits and timeouts: wait and try again
            time.sleep(2 * (attempt + 1))
    sys.exit("HyperSync kept failing")


if len(sys.argv) == 3:
    start, end = int(sys.argv[1]), int(sys.argv[2])
else:
    end = json.load(urllib.request.urlopen(urllib.request.Request(URL + "/height", headers=HEADERS), timeout=30))["height"]
    start = end - 7200

top, seen, block = [], 0, start  # a min-heap keeps only the 10 largest fees
while block <= end:
    r = post({"from_block": block, "to_block": end + 1, "transactions": [{}],
              "field_selection": {"transaction": ["hash", "from", "to", "gas_used", "effective_gas_price", "block_number", "status"]}})
    for page in r["data"]:
        for tx in page["transactions"]:
            seen += 1
            if tx.get("gas_used") is None or tx.get("effective_gas_price") is None:
                continue
            fee = num(tx["gas_used"]) * num(tx["effective_gas_price"])
            item = (fee, tx["hash"], tx.get("to"), num(tx["gas_used"]), num(tx["effective_gas_price"]), num(tx["block_number"]))
            if len(top) < 10:
                heapq.heappush(top, item)
            elif fee > top[0][0]:
                heapq.heapreplace(top, item)
    if r["next_block"] <= block:
        break
    block = r["next_block"]

print(f"Ethereum transactions, blocks {start:,} to {end:,}: {seen:,} scanned\n")
for rank, (fee, tx, to, gas, price, blk) in enumerate(sorted(top, reverse=True), 1):
    base = post({"from_block": blk, "to_block": blk + 1, "include_all_blocks": True,
                 "field_selection": {"block": ["number", "base_fee_per_gas"]}})["data"][0]["blocks"][0]
    ratio = price / num(base["base_fee_per_gas"])
    print(f"{rank:>2}  {fee / 1e18:.4f} ETH  {gas:>9,} gas  {price / 1e9:>7,.0f} gwei  {ratio:>9,.0f}x the base fee  {tx}")
