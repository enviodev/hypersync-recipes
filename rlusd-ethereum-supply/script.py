"""RLUSD supply on Ethereum, day by day, from every mint and burn.

Reads every Transfer event of Ripple USD (RLUSD) on Ethereum with Envio HyperSync,
treats transfers from the zero address as mints and to the zero address as burns,
and prints the running supply, the change over the last 30 days and the current
number of holders.
"""
import collections, datetime, json, os, sys, time, urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN")
HS = "https://eth.hypersync.xyz"
RLUSD = "0x8292bb45bf1ee4d140127049757c2e0ff06317ed"  # Ripple USD on Ethereum (Ripple docs)
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64
START = 20_900_000  # before the RLUSD contract was deployed
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30


def post(body):
    for attempt in range(15):
        try:
            req = urllib.request.Request(HS + "/query", json.dumps(body).encode(),
                                         {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise SystemExit("HyperSync request failed")


logs, block_ts = [], {}
body = {"from_block": START,
        "logs": [{"address": [RLUSD], "topics": [[TRANSFER]]}],
        "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data", "block_number"],
                            "block": ["number", "timestamp"]}}
while True:
    r = post(body)
    for batch in r["data"]:
        for b in batch.get("blocks") or []:
            ts = b["timestamp"]
            block_ts[b["number"]] = int(ts, 16) if isinstance(ts, str) else ts
        for log in batch.get("logs") or []:
            # default join only; keep exactly the token and event we asked for
            if log["address"].lower() == RLUSD and log["topic0"] == TRANSFER:
                logs.append(log)
    if r["next_block"] >= r["archive_height"]:
        break
    body["from_block"] = r["next_block"]

end = max(block_ts.values())
cut = end - DAYS * 86400
day = lambda ts: datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
supply, then = 0, None
daily = collections.OrderedDict()
bal = collections.Counter()
minted = burned = 0
mint_to = collections.Counter()
for log in sorted(logs, key=lambda l: (l["block_number"])):
    ts = block_ts[log["block_number"]]
    if then is None and ts >= cut:
        then = supply
    v = int(log["data"], 16) / 1e18
    frm, to = log["topic1"], log["topic2"]
    if frm == ZERO:
        supply += v
        if ts >= cut:
            minted += v; mint_to["0x" + to[-40:]] += v
    else:
        bal[frm] -= v
    if to == ZERO:
        supply -= v
        if ts >= cut: burned += v
    else:
        bal[to] += v
    daily[day(ts)] = supply
then = supply if then is None else then

holders = sum(1 for a, b in bal.items() if b > 1e-9)
print(f"RLUSD on Ethereum, {len(logs):,} transfers, up to {datetime.datetime.fromtimestamp(end, datetime.timezone.utc):%d %b %Y %H:%M} UTC")
print(f"Supply now {supply/1e6:,.1f}M, {DAYS} days ago {then/1e6:,.1f}M, change {(supply-then)/1e6:+,.1f}M ({100*(supply-then)/then:+.0f}%)")
print(f"Minted {minted/1e6:,.1f}M and burned {burned/1e6:,.1f}M in the last {DAYS} days")
print(f"Holders with a balance: {holders:,}")
print("Top mint recipients in the window:")
for a, v in mint_to.most_common(5):
    print(f"  {a}  {v/1e6:,.1f}M")
json.dump(daily, open(os.environ.get("RLUSD_OUT", "/dev/null"), "w"))
