# Stablecoins on Arc: USDC and EURC supply now, 7 and 30 days ago, with Envio HyperSync.
# Supply is rebuilt from every mint (Transfer from the zero address) and burn (Transfer to it).
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request

URL = "https://arc.hypersync.xyz"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64
# Mainnet addresses from https://docs.arc.io/arc/references/contract-addresses (both use 6 decimals)
TOKENS = {
    "0x3600000000000000000000000000000000000000": "USDC",
    "0xbef5f6d51cb62b58e6a8f77868681825c6fe21c1": "EURC",
}
# USDC is Arc's native asset. totalSupply() on Arc is 10,000 USDC above mints minus burns at every
# block we checked, from block 1000 onwards: a genesis balance that has no Transfer log.
GENESIS = {"USDC": 10_000 * 10**6}
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
END = (int(datetime.datetime.fromisoformat(sys.argv[1]).replace(tzinfo=datetime.timezone.utc).timestamp())
       if len(sys.argv) > 1 else None)  # optional end time in UTC, e.g. 2026-11-09T10:41


def query(body):
    req = urllib.request.Request(URL + "/query", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(2 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


addrs = list(TOKENS)
body = {
    "from_block": 0,
    "logs": [{"address": addrs, "topics": [[TRANSFER], [ZERO]]},
             {"address": addrs, "topics": [[TRANSFER], [], [ZERO]]}],
    "field_selection": {"block": ["number", "timestamp"],
                        "log": ["block_number", "address", "topic0", "topic1", "topic2", "data"]},
}
rows = []
while True:
    res = query(body)
    for batch in res["data"]:
        ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
              for b in batch.get("blocks") or []}
        for log in batch.get("logs") or []:
            name = TOKENS.get(log["address"].lower())
            if not name or log["topic0"].lower() != TRANSFER:
                continue
            value = int(log["data"], 16) if log["data"] != "0x" else 0
            sign = 1 if log["topic1"] == ZERO else -1 if log["topic2"] == ZERO else 0
            rows.append((ts[log["block_number"]], log["block_number"], name, sign, value))
    if res["next_block"] >= res["archive_height"]:
        break
    body["from_block"] = res["next_block"]

end = END or max(r[0] for r in rows)
last_block = max(r[1] for r in rows if r[0] <= end)
fmt = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%d %b %H:%M UTC")
m = lambda v: f"{v / 1e6 / 1e9:.3f}B" if abs(v) >= 1e15 else f"{v / 1e6 / 1e6:,.1f}M"


def supply_at(name, t):
    return GENESIS.get(name, 0) + sum(s * v for ts, _, n, s, v in rows if n == name and ts <= t)


print(f"Stablecoins on Arc, up to {fmt(end)} (last mint or burn in block {last_block:,})")
for name in TOKENS.values():
    now, d7, d30 = (supply_at(name, end - d * 86400) for d in (0, 7, 30))
    minted = sum(v for ts, _, n, s, v in rows if n == name and s > 0 and end - 30 * 86400 < ts <= end)
    burned = sum(v for ts, _, n, s, v in rows if n == name and s < 0 and end - 30 * 86400 < ts <= end)
    print(f"{name}: {m(now)} now, {m(d7)} 7 days ago, {m(d30)} 30 days ago")
    print(f"      30 days: +{m(now - d30)} net, {m(minted)} minted, {m(burned)} burned")

print("\nUSDC supply at the end of each UTC day, last 31 days")
day = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")
supply, by_day = GENESIS["USDC"], {}
for ts, _, n, s, v in sorted(rows):
    if n == "USDC" and ts <= end:
        supply += s * v
        by_day[day(ts)] = supply
days = sorted(by_day)[-31:]
for d in days:
    print(f"  {d}  {m(by_day[d])}")
best = max(zip(days[1:], days), key=lambda p: by_day[p[0]] - by_day[p[1]])
print(f"Biggest one-day rise: {best[0]}, +{m(by_day[best[0]] - by_day[best[1]])}")
