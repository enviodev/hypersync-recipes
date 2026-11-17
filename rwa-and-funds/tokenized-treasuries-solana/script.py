# Tokenized Treasury funds on Solana, with Envio HyperSync.
# Reads every token balance change of the five largest funds' mints, then rebuilds each fund's supply day by day.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HYPERSYNC = "https://solana.hypersync.xyz"
RPC = "https://api.mainnet-beta.solana.com"
# Mint addresses as listed on each fund's page at https://app.rwa.xyz/networks/solana
FUNDS = {
    "JLTXX (J.P. Morgan)": "J4cTuCH6frt4AnEmKfMS2k8hsUf7K94PV62sjUJno8Cz",
    "BUIDL (BlackRock)": "GyWgeqpy5GueU2YbkE8xqUeVEokCMMCEeUrfbtMw6phr",
    "SHVon (Ondo)": "XDZNiWPHH8fyb8PCyTeiJsVsBnBhkBZbcYoxvVpondo",
    "SWEEP (State Street, Galaxy)": "AgBSDfS7CNRunBeREHHdF9S57fai5b3EXH1hgvZkRPhB",
    "USDY (Ondo)": "A1KLoBrKBde8Ty9qtNQUtq3C2ortoC3u7twggz7sEto6",
}
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 65

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(url, body, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, json.dumps(body).encode(), headers)
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def pull(start, end):
    """Every balance change of the fund mints from start up to end (None runs to the head)."""
    body = {"from_slot": start, **({"to_slot": end} if end else {}),
            "account_activity": [{"mint": list(FUNDS.values())}],
            "field_selection": {"account_activity": ["slot", "mint", "pre_token_balance", "post_token_balance"],
                                "block": ["slot", "block_time"]}}
    rows, times = [], {}
    while end is None or body["from_slot"] < end:
        res = post(HYPERSYNC + "/query", body)
        for batch in res.get("blocks") or []:
            for b in batch:
                times[b["slot"]] = b["block_time"]
        for batch in res.get("account_activity") or []:
            rows += [r for r in batch if r.get("mint") in FUNDS.values()]
        if res["next_slot"] <= body["from_slot"]:
            break
        body["from_slot"] = res["next_slot"]
    return [(times[r["slot"]], r) for r in rows]


height = json.load(urllib.request.urlopen(HYPERSYNC + "/height"))  # a bare slot number on Solana


def block_time(slot):
    res = post(HYPERSYNC + "/query", {"from_slot": slot, "to_slot": slot + 50, "include_all_blocks": True,
                                      "field_selection": {"block": ["slot", "block_time"]}})
    return next(b["block_time"] for batch in res["blocks"] for b in batch if b.get("block_time"))


# Measure the recent slot rate, then start a day early so the first day is complete.
rate = 1_000_000 / (block_time(height - 1000) - block_time(height - 1_001_000))
start = height - int((DAYS + 1) * 86400 * rate)
step = 500_000
ranges = [(s, s + step if s + step < height else None) for s in range(start, height, step)]
print(f"Reading {len(ranges)} slot ranges from HyperSync...", file=sys.stderr)
with ThreadPoolExecutor(16) as pool:
    rows = [r for part in pool.map(lambda a: pull(*a), ranges) for r in part]

# Supply now, from Solana RPC, then walk back through each day's net mints and burns.
supply, decimals = {}, {}
for name, mint in FUNDS.items():
    v = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply", "params": [mint]}, auth=False)["result"]["value"]
    supply[name], decimals[name] = int(v["amount"]), v["decimals"]

by_mint = {m: n for n, m in FUNDS.items()}
net = defaultdict(lambda: defaultdict(int))
for ts, r in rows:
    change = int(r.get("post_token_balance") or 0) - int(r.get("pre_token_balance") or 0)
    day = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).date()
    net[by_mint[r["mint"]]][day] += change

today = datetime.datetime.now(datetime.timezone.utc).date()
days = [today - datetime.timedelta(d) for d in range(DAYS - 2, -1, -7)]
print("Fund supply in tokens at the end of each week")
print("".ljust(30) + "".join(f"{d:%d %b}".rjust(9) for d in days))
for name in FUNDS:
    cells = []
    for d in days:
        after = sum(v for k, v in net[name].items() if k > d)
        cells.append(f"{(supply[name] - after) / 10 ** decimals[name] / 1e6:8.1f}M")
    print(name.ljust(30) + " ".join(cells))
