# USDC supply on Ethereum, day by day, with Envio HyperSync.
# Every USDC Transfer from or to the zero address is a mint or a burn.
# Prints net USDC minted or burned per UTC day and the total. Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

URL = "https://eth.hypersync.xyz"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # https://developers.circle.com/stablecoins/usdc-contract-addresses
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(path, body=None):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def as_int(v):
    return int(v, 16) if isinstance(v, str) else v


# Blocks are about 12 seconds, so start a little more than DAYS back and trim by timestamp.
height = post("/height")["height"]
start = height - (DAYS + 2) * 7200
cutoff = datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=DAYS)

body = {
    "from_block": start,
    "logs": [{"address": [USDC], "topics": [[TRANSFER], [ZERO]]},
             {"address": [USDC], "topics": [[TRANSFER], [], [ZERO]]}],
    "field_selection": {"block": ["number", "timestamp"],
                        "log": ["block_number", "address", "topic0", "topic1", "topic2", "data"]},
}
usdc = defaultdict(int)
minted = defaultdict(int)
burned = defaultdict(int)
while True:
    res = post("/query", body)
    for batch in res["data"]:
        ts = {b["number"]: as_int(b["timestamp"]) for b in batch.get("blocks") or []}
        for log in batch.get("logs") or []:
            day = datetime.datetime.fromtimestamp(ts[log["block_number"]], datetime.timezone.utc).date()
            a, t0 = log["address"].lower(), log["topic0"]
            if a == USDC and t0 == TRANSFER:
                v = int(log["data"], 16)
                if log["topic1"] == ZERO:
                    usdc[day] += v
                    minted[day] += v
                elif log["topic2"] == ZERO:
                    usdc[day] -= v
                    burned[day] += v
    if res["next_block"] >= res["archive_height"]:
        break
    body["from_block"] = res["next_block"]

# Optional second argument: an end date (YYYY-MM-DD, exclusive) to rerun a past window exactly.
end = datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else None
if end:
    cutoff = end - datetime.timedelta(days=DAYS)
days = [d for d in sorted(usdc) if d >= cutoff and (end is None or d < end)]
print(f"Net USDC minted or burned on Ethereum per UTC day, {days[0]:%d %b} to {days[-1]:%d %b}")
for day in days:
    print(f"{day:%d %b}  {usdc[day] / 1e12:>+9.1f}M USDC")
m, b = sum(minted[d] for d in days), sum(burned[d] for d in days)
print(f"Minted  {m / 1e15:>7.2f}B USDC")
print(f"Burned  {b / 1e15:>7.2f}B USDC")
print(f"Total moved in and out  {(m + b) / 1e15:.2f}B USDC, net {(m - b) / 1e15:+.2f}B")
