# Depositors in the USDG vault behind Robinhood Earn, with Envio HyperSync.
# Reads every ERC-4626 Deposit and Withdraw on the Steakhouse USDG Morpho vault on Robinhood (chain 4663),
# counts unique depositing wallets, deposits per day and typical deposit size, then checks the net flow
# against the vault's live totalAssets read over RPC. Writes daily rows to daily.json.
# Python 3.9+ standard library only. Set ENVIO_API_TOKEN first.
#
#   python script.py            pull every event, save it to rows.json, print the numbers
#   python script.py --cached   reuse rows.json from an earlier run
import collections
import datetime
import json
import os
import statistics
import sys
import time
import urllib.request

URL = "https://robinhood.hypersync.xyz"
RPC = "https://rpc.mainnet.chain.robinhood.com"
# Steakhouse USDG (steakUSDG), the Morpho vault curated by Steakhouse Financial behind Robinhood Earn.
# Linked by Steakhouse at https://kitchen.steakhouse.financial/p/defi-markets-update-2026-09-01
VAULT = "0xbeeff033f34c046626b8d0a041844c5d1a5409dd"
# USDG on Robinhood, from https://docs.robinhood.com/chain/contracts/ (6 decimals)
USDG = "0x5fc5360d0400a0fd4f2af552add042d716f1d168"
# Deposit(address indexed sender, address indexed owner, uint256 assets, uint256 shares)
DEPOSIT = "0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7"
# Withdraw(address indexed sender, address indexed receiver, address indexed owner, uint256 assets, uint256 shares)
WITHDRAW = "0xfbde797d201c681b91056529119e0b02407c7bb96a4a2c75c01fc9667232c8db"

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(url, body, auth=True):
    headers = {"Content-Type": "application/json", "User-Agent": "curl/8"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception as e:  # retry transient network errors
            if attempt == 7:
                raise
            time.sleep(2 * (attempt + 1))


def num(x):
    return int(x, 16) if isinstance(x, str) else x


# One query for both events. HyperSync's default join returns each log's block and transaction.
query = {
    "from_block": 0,
    "logs": [{"address": [VAULT], "topics": [[DEPOSIT, WITHDRAW]]}],
    "field_selection": {
        "block": ["number", "timestamp"],
        "transaction": ["hash", "from"],
        "log": ["block_number", "transaction_hash", "log_index", "address", "topic0", "topic1", "topic2", "topic3", "data"],
    },
}
rows = []
CACHED = "--cached" in sys.argv and os.path.exists("rows.json")
if CACHED:
    saved = json.load(open("rows.json"))
    rows, res = saved["rows"], {"archive_height": saved["height"]}
while not CACHED:
    res = post(URL + "/query", query)
    for batch in res["data"]:
        ts = {num(b["number"]): num(b["timestamp"]) for b in batch.get("blocks") or []}
        sender = {t["hash"]: t["from"].lower() for t in batch.get("transactions") or []}
        for log in batch.get("logs") or []:
            # keep only logs whose address and topic0 match exactly
            if log["address"].lower() != VAULT or log["topic0"] not in (DEPOSIT, WITHDRAW):
                continue
            data = log["data"][2:]
            dep = log["topic0"] == DEPOSIT
            owner = (log["topic2"] if dep else log["topic3"])[-40:]
            rows.append({
                "kind": "deposit" if dep else "withdraw",
                "block": num(log["block_number"]),
                "ts": ts[num(log["block_number"])],
                "tx": log["transaction_hash"],
                "tx_from": sender.get(log["transaction_hash"], ""),
                "owner": "0x" + owner,
                "assets": int(data[0:64], 16) / 1e6,
            })
    if res["next_block"] >= res["archive_height"]:
        break
    query["from_block"] = res["next_block"]
height = res["archive_height"]
if not CACHED:
    json.dump({"height": height, "rows": rows}, open("rows.json", "w"))

deps = [r for r in rows if r["kind"] == "deposit"]
wds = [r for r in rows if r["kind"] == "withdraw"]
day = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")

# Daily series: deposits, new depositing wallets, flows
seen = set()
daily = collections.OrderedDict()
for r in sorted(rows, key=lambda r: (r["block"], r["kind"])):
    d = daily.setdefault(day(r["ts"]), {"deposits": 0, "new_wallets": 0, "wallets": set(), "in": 0.0, "out": 0.0})
    if r["kind"] == "deposit":
        d["deposits"] += 1
        d["in"] += r["assets"]
        d["wallets"].add(r["owner"])
        if r["owner"] not in seen:
            seen.add(r["owner"])
            d["new_wallets"] += 1
    else:
        d["out"] += r["assets"]
cum_w, cum_net, out = 0, 0.0, []
for k, d in daily.items():
    cum_w += d["new_wallets"]
    cum_net += d["in"] - d["out"]
    out.append({"day": k, "deposits": d["deposits"], "active_wallets": len(d["wallets"]), "new_wallets": d["new_wallets"],
                "total_wallets": cum_w, "in": round(d["in"], 2), "out": round(d["out"], 2), "net_supplied": round(cum_net, 2)})
json.dump({"vault": VAULT, "height": height, "daily": out}, open("daily.json", "w"), indent=1)

# Wash check: wallets that deposit and withdraw the same amount within a day, over and over
per_owner = collections.defaultdict(list)
for r in rows:
    per_owner[r["owner"]].append(r)
cyclers = set()
for o, rs in per_owner.items():
    days = collections.Counter((day(r["ts"]), r["kind"]) for r in rs)
    busy = [k for (k, kind), n in days.items() if kind == "deposit" and n >= 20 and days.get((k, "withdraw"), 0) >= 20]
    if busy:
        cyclers.add(o)

sizes = sorted(r["assets"] for r in deps)
per_wallet = collections.defaultdict(float)
for r in deps:
    per_wallet[r["owner"]] += r["assets"]
wallet_totals = sorted(per_wallet.values())
total_in = sum(sizes)
total_out = sum(r["assets"] for r in wds)

# Second method: the vault's own totalAssets() over RPC (selector 0x01e1d114)
live = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                  "params": [{"to": VAULT, "data": "0x01e1d114"}, "latest"]}, auth=False)
total_assets = int(live["result"], 16) / 1e6

print(f"Steakhouse USDG vault {VAULT} on Robinhood, blocks up to {height:,}")
print(f"First deposit {day(deps[0]['ts'])}, last {day(deps[-1]['ts'])}")
print(f"Deposits {len(deps):,} from {len(per_wallet):,} wallets. Withdrawals {len(wds):,}")
print(f"Supplied in total ${total_in:,.0f}, withdrawn ${total_out:,.0f}, net ${total_in - total_out:,.0f}")
print(f"Vault totalAssets() now ${total_assets:,.0f} (net flow plus interest earned)")
print(f"Median deposit ${statistics.median(sizes):,.2f}, mean ${total_in / len(sizes):,.0f}")
print(f"Median total deposited per wallet ${statistics.median(wallet_totals):,.2f}")
for cut in (100, 1_000, 10_000, 1_000_000):
    n = sum(1 for v in wallet_totals if v < cut)
    print(f"  wallets that deposited under ${cut:>9,}: {n:>7,} ({n / len(wallet_totals):.0%})")
top = sum(sorted(wallet_totals, reverse=True)[:10])
print(f"Top 10 wallets put in ${top:,.0f} ({top / total_in:.0%} of all deposits)")
print(f"Wash check: {len(cyclers)} wallets with 20+ deposits and 20+ withdrawals in one day")
