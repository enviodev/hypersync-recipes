# Yield Basis yb-WETH propAMM on Ethereum, first week, with Envio HyperSync.
# Finds the moment the crvUSD/WETH pool switched to oracle pricing (Yield Basis proposal #60 and Curve vote 1508
# installed the YBOraclizedPolicy contract), then reads every swap in the 7 days after and the 7 days before.
# Prints volume, fees, wallets, the busiest day and hour, the largest swap and how much of the volume came from
# the most active wallets. Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import datetime
import json
import os
import sys
import time
import urllib.request

POOL = "0x656341ef90b622c6634e0573772ffb7f3669b9f3"  # Yield Basis WETH (YB-WETH), crvUSD/WETH, market 10
TOKEN_EXCHANGE = "0x143f1f8e861fbdeddd5b46e844b7d3ac7b86a122f36e8c463859ee6811b1f29c"
SET_POLICY = "0x78e81206388ab3ee5e73c68b87da16f8cc8968c831d517adec68a516c75d09b0"  # SetPolicyContract(address)
WEEK = 7 * 86400
MIN_USD = 1  # skip zero-size calls (1 wei pokes), which are not trades

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def query(body):
    req = urllib.request.Request("https://eth.hypersync.xyz/query", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def logs(topic, from_block):
    body = {"from_block": from_block, "logs": [{"address": [POOL], "topics": [[topic]]}],
            "field_selection": {"log": ["block_number", "log_index", "topic1", "data", "transaction_hash"],
                                "block": ["number", "timestamp"], "transaction": ["hash", "from"]}}
    out, ts, sender = [], {}, {}
    while True:
        res = query(body)
        for batch in res["data"]:
            out += batch.get("logs") or []
            ts.update({b["number"]: int(b["timestamp"], 16) for b in batch.get("blocks") or []})
            sender.update({t["hash"]: t["from"] for t in batch.get("transactions") or []})
        if res["next_block"] >= res["archive_height"]:
            return out, ts, sender, res["archive_height"]
        body["from_block"] = res["next_block"]


def utc(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# 1. When did the pool start pricing off oracle reports? The last SetPolicyContract on the pool.
policy_logs, policy_ts, _, _ = logs(SET_POLICY, 0)
launch_log = max(policy_logs, key=lambda l: (l["block_number"], l["log_index"]))
launch = policy_ts[launch_log["block_number"]]
end = launch + WEEK

# 2. Every swap from a week before the switch onwards
swap_logs, ts, sender, head = logs(TOKEN_EXCHANGE, launch_log["block_number"] - 60000)
if max(ts.values()) < end - 3600:
    print("Note: the first week is not over yet, so the numbers below are partial")
swaps = []
for log in swap_logs:
    t = ts[log["block_number"]]
    if not launch - WEEK <= t < end:
        continue
    sold_id, sold, bought_id, bought, fee = (int(log["data"][2 + 64 * i: 66 + 64 * i], 16) for i in range(5))
    usd = (sold if sold_id == 0 else bought) / 1e18   # coin 0 is crvUSD, valued at $1
    eth = (sold if sold_id == 1 else bought) / 1e18   # coin 1 is WETH
    if usd < MIN_USD:
        continue
    fee_usd = fee / 1e18 if bought_id == 0 else fee / 1e18 * usd / eth  # fee is paid in the coin bought
    swaps.append({"t": t, "usd": usd, "fee": fee_usd, "wallet": sender[log["transaction_hash"]],
                  "tx": log["transaction_hash"], "fee_crvusd": fee / 1e18 if bought_id == 0 else 0,
                  "fee_weth": fee / 1e18 if bought_id == 1 else 0})

before = [s for s in swaps if s["t"] < launch]
week = [s for s in swaps if s["t"] >= launch]
vol, fees = sum(s["usd"] for s in week), sum(s["fee"] for s in week)
vol_before = sum(s["usd"] for s in before)

print("Yield Basis yb-WETH propAMM, first 7 days")
print(f"  Oracle pricing live from {utc(launch)} (block {launch_log['block_number']})")
print(f"  Volume  ${vol / 1e6:.1f}M   ({vol / vol_before:.1f}x the ${vol_before / 1e6:.1f}M of the 7 days before)")
print(f"  Fees    {sum(s['fee_crvusd'] for s in week):,.0f} crvUSD + {sum(s['fee_weth'] for s in week):.2f} WETH, "
      f"${fees / 1e3:.0f}K with WETH at each swap's price")
print(f"  Swaps   {len(week)}   Wallets {len({s['wallet'] for s in week})}")

print("  By day (24 hours from the switch)")
days = collections.defaultdict(lambda: [0.0, 0.0, 0, set()])
for s in week:
    d = days[(s["t"] - launch) // 86400]
    d[0] += s["usd"]; d[1] += s["fee"]; d[2] += 1; d[3].add(s["wallet"])
for i in range(7):
    v, f, n, w = days[i]
    print(f"    day {i + 1}  ${v / 1e6:6.2f}M volume  ${f / 1e3:6.1f}K fees  {n:3} swaps  {len(w):2} wallets")
print(f"  Day 1 share: {100 * days[0][0] / vol:.0f}% of volume, {100 * days[0][1] / fees:.0f}% of fees")

hours, since = collections.Counter(), collections.Counter()
for s in week:
    hours[s["t"] // 3600 * 3600] += s["usd"]
    since[(s["t"] - launch) // 3600] += s["usd"]
peak, peak_vol = hours.most_common(1)[0]
print(f"  Busiest clock hour  ${peak_vol / 1e6:.1f}M  from {utc(peak)}")
big = max(week, key=lambda s: s["usd"])
print(f"  Largest swap  ${big['usd'] / 1e6:.2f}M with ${big['fee'] / 1e3:.0f}K fee  {big['tx']}")

by_wallet = collections.Counter()
for s in week:
    by_wallet[s["wallet"]] += s["usd"]
top = [v for _, v in by_wallet.most_common()]
print(f"  Top wallet {100 * top[0] / vol:.0f}%, top 5 {100 * sum(top[:5]) / vol:.0f}%, "
      f"top 10 {100 * sum(top[:10]) / vol:.0f}% of volume")

if "--hourly" in sys.argv:  # volume per hour since the switch, 168 values (7 days x 24 hours), for charting
    print(json.dumps([round(since[h]) for h in range(168)]))
