# PAXG on Morpho, Base: every market that lends USDC against Paxos Gold, and what happened in it.
# Finds the markets with Envio HyperSync (every Morpho CreateMarket event on Base whose collateral is PAXG),
# then reads every collateral, borrow, repay, supply and liquidation event in them, plus every PAXG mint
# and burn on Base. Live state (totalBorrowAssets, oracle price) is read from Base's public RPC to check the sums.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
#   python script.py              # full history up to now
#   python script.py 55200000     # stop at a fixed Base block to rerun a past snapshot exactly
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

HYPERSYNC = "https://base.hypersync.xyz"
RPC = "https://mainnet.base.org"
MORPHO = "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb"  # https://docs.morpho.org/get-started/resources/addresses
PAXG = "0xe904aea5e1b110c9174728fa2effc8aed19e98ef"    # https://docs.paxos.com/guides/stablecoin/paxg/mainnet
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
ZERO = "0x" + "0" * 64

T = {  # Morpho event signatures (topic0)
    "CreateMarket": "0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac",
    "SupplyCollateral": "0xa3b9472a1399e17e123f3c2e6586c23e504184d504de59cdaa2b375e880c6184",
    "WithdrawCollateral": "0xe80ebd7cc9223d7382aab2e0d1d6155c65651f83d53c8b9b06901d167e321142",
    "Borrow": "0x570954540bed6b1304a87dfe815a5eda4a648f7097a16240dcd85c9b5fd42a43",
    "Repay": "0x52acb05cebbd3cd39715469f22afbf5a17496295ef3bc9bb5944056c63ccaa09",
    "Liquidate": "0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41",
    "Supply": "0xedf8870433c83823eb071d3df1caa8d008f12f6440918c20d75a3602cda30fe0",
    "Withdraw": "0xa56fc0ad5702ec05ce63666221f796fb62437c32db1aa1aa075fc6484cf58fbf",
}
NAME = {v: k for k, v in T.items()}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
TO_BLOCK = int(sys.argv[1]) if len(sys.argv) > 1 else None


def request(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def call(to, data, block):
    tag = hex(block) if block else "latest"
    res = request(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, tag]},
                  {"User-Agent": "Mozilla/5.0"})
    return res.get("result", "0x")[2:]


def logs(selection, from_block):
    """Every matching log with its block timestamp, paging through HyperSync until the chain tip (or TO_BLOCK)."""
    body = {"from_block": from_block, "logs": [selection],
            "field_selection": {"log": ["block_number", "log_index", "address", "topic0", "topic1", "topic2", "topic3", "data"],
                                "block": ["number", "timestamp"]}}
    if TO_BLOCK:
        body["to_block"] = TO_BLOCK + 1
    out, height = [], 0
    while True:
        res = request(HYPERSYNC + "/query", body, {"Authorization": "Bearer " + TOKEN})
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                if log["address"].lower() != selection["address"][0]:
                    continue
                if log["topic0"] not in selection["topics"][0]:
                    continue
                log["time"] = ts[log["block_number"]]
                out.append(log)
        height = res["next_block"]
        if TO_BLOCK and height > TO_BLOCK:
            break
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]
    return out, height


def words(data):
    return [int(data[2 + i:66 + i], 16) for i in range(0, len(data) - 2, 64)]


def addr(topic):
    return "0x" + topic[-40:]


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


# 1. Find every Morpho market on Base that takes PAXG as collateral.
created, _ = logs({"address": [MORPHO], "topics": [[T["CreateMarket"]]]}, 0)
markets = {}
for log in created:
    w = log["data"][2:]
    loan, coll, lltv = "0x" + w[24:64], "0x" + w[88:128], int(w[256:320], 16)
    if coll == PAXG:
        markets[log["topic1"]] = dict(loan=loan, oracle="0x" + w[152:192], lltv=lltv / 1e18,
                                      block=log["block_number"], time=log["time"])
first = min(m["block"] for m in markets.values())

# 2. Every event in those markets.
events, height = logs({"address": [MORPHO], "topics": [list(NAME), list(markets)]}, first)
events.sort(key=lambda l: (l["block_number"], int(l["log_index"], 16) if isinstance(l["log_index"], str) else l["log_index"]))
snapshot = (TO_BLOCK or height - 1)

print(f"PAXG on Morpho, Base, up to block {snapshot:,}")
print(f"{len(markets)} markets take PAXG as collateral (Morpho {MORPHO}, PAXG {PAXG})\n")

per = {m: defaultdict(float) for m in markets}
borrowers = {m: set() for m in markets}
collateral_by_user = {m: defaultdict(float) for m in markets}
borrow_by_user = {m: defaultdict(float) for m in markets}
daily = defaultdict(lambda: defaultdict(float))
for log in events:
    m, kind, w = log["topic1"], NAME[log["topic0"]], words(log["data"])
    p = per[m]
    p[kind + "_count"] += 1
    if kind == "SupplyCollateral":
        amount = w[0] / 1e18
        p["collateral_in"] += amount
        collateral_by_user[m][addr(log["topic3"])] += amount
        daily[day(log["time"])][m + "coll"] += amount
    elif kind == "WithdrawCollateral":
        amount = w[1] / 1e18
        p["collateral_out"] += amount
        collateral_by_user[m][addr(log["topic2"])] -= amount
        daily[day(log["time"])][m + "coll"] -= amount
    elif kind == "Borrow":
        p["borrowed"] += w[1] / 1e6
        borrowers[m].add(addr(log["topic2"]))
        borrow_by_user[m][addr(log["topic2"])] += w[1] / 1e6
        daily[day(log["time"])][m + "debt"] += w[1] / 1e6
    elif kind == "Repay":
        p["repaid"] += w[0] / 1e6
        daily[day(log["time"])][m + "debt"] -= w[0] / 1e6
    elif kind == "Liquidate":
        p["liq_repaid"] += w[0] / 1e6
        p["liq_seized"] += w[2] / 1e18
        p["bad_debt"] += w[3] / 1e6
        collateral_by_user[m][addr(log["topic3"])] -= w[2] / 1e18
        daily[day(log["time"])][m + "coll"] -= w[2] / 1e18
        daily[day(log["time"])][m + "debt"] -= (w[0] + w[3]) / 1e6
    elif kind == "Supply":
        p["supplied"] += w[0] / 1e6
    elif kind == "Withdraw":
        p["withdrawn"] += w[1] / 1e6

# 3. Live state from RPC, to check the event sums and price the collateral.
block = TO_BLOCK
rows = []
for m, info in sorted(markets.items(), key=lambda kv: kv[1]["block"]):
    s = call(MORPHO, "0x5c60e39a" + m[2:], block)          # market(bytes32)
    supply_assets, borrow_assets = int(s[0:64], 16) / 1e6, int(s[128:192], 16) / 1e6
    price = int(call(info["oracle"], "0xa035b1fe", block) or "0", 16) / 1e24  # price(), USDC per PAXG
    p = per[m]
    coll = p["collateral_in"] - p["collateral_out"] - p["liq_seized"]
    holders = sum(1 for v in collateral_by_user[m].values() if v > 1e-12)
    rows.append((coll * price, m))
    print(f"Market {m}")
    print(f"  created {day(info['time'])} (block {info['block']:,}), loan USDC, LLTV {info['lltv']:.0%}, oracle {info['oracle']}")
    print(f"  PAXG collateral: {coll:,.4f} now ({p['collateral_in']:,.4f} in, {p['collateral_out']:,.4f} out, "
          f"{p['liq_seized']:,.4f} seized) ~ ${coll * price:,.0f} at ${price:,.0f} per PAXG")
    print(f"  USDC borrowed: {p['borrowed']:,.2f} in total, {p['repaid'] + p['liq_repaid']:,.2f} repaid, "
          f"{borrow_assets:,.2f} owed now with interest (RPC)")
    print(f"  USDC supplied by lenders now: {supply_assets:,.2f}  ({borrow_assets / supply_assets:.0%} lent out)" if supply_assets else
          "  USDC supplied by lenders now: 0")
    print(f"  {len(borrowers[m])} unique borrowers, {holders} wallets with collateral now, "
          f"{int(p['Liquidate_count'])} liquidations, {int(sum(v for k, v in p.items() if k.endswith('_count')))} events\n")

main = max(rows)[1]
print(f"Biggest market by collateral: {main}")
all_borrowers = set().union(*borrowers.values())
total_coll = sum(per[m]["collateral_in"] - per[m]["collateral_out"] - per[m]["liq_seized"] for m in markets)
sizes = sorted(v for v in collateral_by_user[main].values() if v > 1e-12)
loans = sorted(borrow_by_user[main].values())
print(f"  median PAXG per wallet with collateral: {sizes[len(sizes) // 2]:,.4f}, biggest: {sizes[-1]:,.4f} "
      f"({sizes[-1] / sum(sizes):.0%} of the market)")
print(f"  biggest borrower took {loans[-1]:,.2f} USDC ({loans[-1] / sum(loans):.0%} of all borrows), "
      f"median borrower {loans[len(loans) // 2]:,.2f} USDC")
print(f"All PAXG markets: {total_coll:,.4f} PAXG collateral, {len(all_borrowers)} unique borrowers\n")

print("Biggest market, end of each UTC day: PAXG collateral, USDC borrowed principal (borrows minus repays)")
coll = debt = 0.0
for d in sorted(daily):
    coll += daily[d][main + "coll"]
    debt += daily[d][main + "debt"]
    if daily[d][main + "coll"] or daily[d][main + "debt"]:
        print(f"  {d}  {coll:>10,.4f} PAXG  {debt:>12,.2f} USDC")

# 4. PAXG supply on Base: mints are Transfers from zero, burns are Transfers to zero.
mints, _ = logs({"address": [PAXG], "topics": [[TRANSFER], [ZERO]]}, 0)
burns, _ = logs({"address": [PAXG], "topics": [[TRANSFER], [], [ZERO]]}, 0)
minted = sum(int(l["data"], 16) for l in mints) / 1e18
burned = sum(int(l["data"], 16) for l in burns) / 1e18
onchain = int(call(PAXG, "0x18160ddd", block), 16) / 1e18   # totalSupply()
print(f"\nPAXG on Base: {minted - burned:,.4f} from {len(mints)} mints and {len(burns)} burns "
      f"(totalSupply() says {onchain:,.4f}), first mint {day(min(l['time'] for l in mints))}")
print(f"Share of all PAXG on Base sitting as Morpho collateral: {total_coll / onchain:.1%}")
