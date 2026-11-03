# USDC on Arc: every mint and burn, with Envio HyperSync.
# Prints the supply now and N days ago, USDC minted and burned in that window,
# and how much of the burning went through Circle Gateway and CCTP.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request

URL = "https://arc.hypersync.xyz"
USDC = "0x3600000000000000000000000000000000000000"  # USDC on Arc, from docs.arc.io
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64
# From Circle's contract address pages:
# https://developers.circle.com/gateway/references/contract-addresses
# https://developers.circle.com/cctp/references/contract-addresses
CIRCLE = {
    "77777777dcc4d5a8b6e418fd04d8997ef11000ee": "Circle Gateway",
    "fd78ee919681417d192449715b2594ab58f5d002": "CCTP",
}
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
# Optional end time in UTC, e.g. 2026-11-03T09:00, to rerun a past window exactly.
END = (int(datetime.datetime.fromisoformat(sys.argv[2]).replace(tzinfo=datetime.timezone.utc).timestamp())
       if len(sys.argv) > 2 else None)


def query(body):
    req = urllib.request.Request(URL + "/query", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(2 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def as_int(v):
    return int(v, 16) if isinstance(v, str) else v


# Every USDC Transfer from or to the zero address is a mint or a burn.
body = {
    "from_block": 0,
    "logs": [{"address": [USDC], "topics": [[TRANSFER], [ZERO]]},
             {"address": [USDC], "topics": [[TRANSFER], [], [ZERO]]}],
    "field_selection": {"block": ["number", "timestamp"],
                        "log": ["block_number", "address", "topic0", "topic1", "topic2", "data"]},
}
rows = []
while True:
    res = query(body)
    for batch in res["data"]:
        ts = {b["number"]: as_int(b["timestamp"]) for b in batch.get("blocks") or []}
        for log in batch.get("logs") or []:
            if log["address"].lower() != USDC or log["topic0"].lower() != TRANSFER:
                continue
            value = int(log["data"], 16) if log["data"] != "0x" else 0
            rows.append((ts[log["block_number"]], log["topic1"], log["topic2"], value))
    if res["next_block"] >= res["archive_height"]:
        break
    body["from_block"] = res["next_block"]

end = END or max(r[0] for r in rows)
start = end - DAYS * 86400
supply = supply_then = minted = burned = 0
burned_by = {}
for t, frm, to, value in rows:
    if t > end:
        continue
    change = value if frm == ZERO else -value
    supply += change
    if t <= start:
        supply_then += change
    elif frm == ZERO:
        minted += value
    else:
        burned += value
        name = CIRCLE.get(frm[-40:], "other")
        burned_by[name] = burned_by.get(name, 0) + value

usd = lambda v: f"${v / 1e6 / 1e9:.2f}B" if v >= 1e15 else f"${v / 1e6 / 1e6:,.0f}M"
fmt = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%d %b %H:%M UTC")
print(f"USDC on Arc, {DAYS} days from {fmt(start)} to {fmt(end)}")
print(f"Supply then  {usd(supply_then)}")
print(f"Minted       {usd(minted)}")
print(f"Burned       {usd(burned)}")
print(f"Supply now   {usd(supply)}  (net {usd(minted - burned)} added)")
for name in ("Circle Gateway", "CCTP", "other"):
    print(f"  burned via {name:<14} {usd(burned_by.get(name, 0))}")
