# What sits in Sentora's curated markets on Aave v4, with Envio HyperSync.
# Reads every Supply, Withdraw, Borrow, Repay, LiquidationCall and ReportDeficit on Sentora's three Aave v4 spokes
# on Ethereum and rebuilds what is supplied and borrowed from them. Dollar prices come from HyperSync too, from the
# AnswerUpdated logs of the Chainlink aggregators behind each spoke's Aave oracle. A public RPC gives token details,
# the oracle price as a labelled check, and a labelled cross-check against the spokes' own state.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

# Spoke and oracle addresses from Aave's official address book:
# https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4EthereumSentoraCurated.sol
SPOKES = {
    "0x9ebf0c19bf7dfe859820cc09e846114b53814e52": ("RLUSD Yield", "0xB5A140D5209E3bc069cD9BBEA39D0051ee041360"),
    "0xbb97b61ad6747d337e5805f2d159d275bb1f0828": ("OUSD Yield", "0xC03078e957bD139C68984015268dA0F16a571F78"),
    "0xa37e7cdc557f3c7f745fb3f337b6439979662c46": ("Bluechip", "0x5Aa69D0DA40636786Fd72D01E656c81818D0A350"),
}
# Event signatures from Aave's ISpoke interface: https://github.com/aave/aave-v4/blob/main/src/spoke/interfaces/ISpoke.sol
SUPPLY = "0xd986db228cb1fe8392c5f45ff5f2c639b7db6cbd9ca7d1fe70b2de90c2c8c961"    # Supply(uint256,address,address,uint256,uint256)
WITHDRAW = "0xfe7813e2866053d5c3938554e517b554fce6666a6561bed9eaa7419b29fa9b68"  # Withdraw(uint256,address,address,uint256,uint256)
BORROW = "0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"    # Borrow(uint256,address,address,uint256,uint256)
REPAY = "0xd765a0263e8a360da8dd4fdb8c0dc5553adec12a96f29a462cdb45e5bea407dd"     # Repay(uint256,address,address,uint256,uint256,(int256,int256,uint256))
LIQUIDATION = "0x2a1f12d996f530f89d8038aa293f9fde81cac44b6dfd6225e3358d09b78a4a37"  # LiquidationCall(uint256,uint256,address,address,bool,uint256,uint256,(int256,int256,uint256),uint256,uint256,uint256)
DEFICIT = "0x59932f333b3a5e3fec86e662babe8dd767529ed207420e7468bd220cdfb3f076"      # ReportDeficit(uint256,address,uint256,(int256,int256,uint256))
ADD_RESERVE = "0xb2d3221c3db1eb0d586556ae23399acdfe3e52ff0fcd184c19069c730f9ca2e9"  # AddReserve(uint256,uint256,address)
TOPICS = [SUPPLY, WITHDRAW, BORROW, REPAY, LIQUIDATION, DEFICIT, ADD_RESERVE]
ANSWER_UPDATED = "0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f"  # AnswerUpdated(int256 indexed current, uint256 indexed roundId, uint256 updatedAt)
# Chainlink aggregators behind the spokes' oracle adapters, as (aggregator, decimals). Found with each oracle's
# getReserveSource(reserveId), which returns an adapter, then the adapter's price feed proxy and its aggregator().
FEEDS = {
    "RLUSD/USD": ("0x7d95b7bf7bB7750d818F42Df114739B6C88CF9bC", 8),
    "USDe/USD": ("0xcC16f670129f965b396f2e81312F6e339FFDB18e", 8),
    "OUSD/USD": ("0x07cd2979401f63F9DC95657B1529849cfA8440E2", 8),
    "PYUSD/USD": ("0x39E31761911b9aaBAEF5fb81B18Fd1C24a60E884", 8),
    "USDC/USD": ("0x54bCC589d9743E521c64233706FC8cB36D275b07", 8),
    "BTC/USD": ("0x4a3411ac2948B33c69666B35cc6d055B27Ea84f1", 8),
    "MWIN NAV": ("0xF8a4527C373dBcA70b302CE77af255439Fa2A5Df", 8),
    "PRIME/wYLDS rate": ("0x48F9A46BA852B5c22D4153D0534397B59AbfdeF5", 18),
    "PST/USDC rate": ("0x7842fe224A835f5587ac33d321Cb054A7dd65c98", 6),
}
# How each reserve is priced, by reserve id, the way the spoke's oracle builds it. wYLDS is fixed at $1 in the adapter.
PRICING = {
    "RLUSD Yield": {0: ("RLUSD/USD",), 1: ("USDe/USD",), 2: ("PRIME/wYLDS rate",), 3: ("MWIN NAV",), 4: ("PST/USDC rate", "USDC/USD")},
    "OUSD Yield": {0: ("OUSD/USD",), 1: ("USDe/USD",), 2: ("PRIME/wYLDS rate",), 3: ("MWIN NAV",), 4: ("PST/USDC rate", "USDC/USD")},
    "Bluechip": {0: ("RLUSD/USD",), 1: ("PYUSD/USD",), 2: ("OUSD/USD",), 3: ("BTC/USD",)},
}
HYPERSYNC = "https://eth.hypersync.xyz/query"
RPC = "https://ethereum-rpc.publicnode.com"

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(url, body, auth=False):
    headers = {"Content-Type": "application/json", "User-Agent": "curl/8"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    for attempt in range(10):
        try:
            res = json.load(urllib.request.urlopen(req, timeout=180))
            if "error" in res:
                raise ValueError(res["error"])
            return res
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def call(to, selector, arg, block):
    data = selector + format(arg, "064x") if arg is not None else selector
    return post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, block]})["result"]


def word(hexdata, i):
    return int(hexdata[2 + 64 * i: 2 + 64 * (i + 1)], 16)


def symbol(token, block):
    raw = bytes.fromhex(call(token, "0x95d89b41", None, block)[2:])
    return raw[64:64 + int.from_bytes(raw[32:64], "big")].decode()


# 1. Every spoke event since Aave v4 went live on Ethereum, using the default join so only matching logs come back.
body = {
    "from_block": 23_000_000,
    "logs": [{"address": list(SPOKES), "topics": [TOPICS]}],
    "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "topic3", "data", "block_number", "log_index"],
                        "block": ["number", "timestamp"]},
}
logs, times = [], {}
while True:
    res = post(HYPERSYNC, body, auth=True)
    for batch in res["data"]:
        for b in batch.get("blocks") or []:
            times[b["number"]] = int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
        for log in batch.get("logs") or []:
            if log["address"].lower() in SPOKES and log["topic0"] in TOPICS:  # keep only what we asked for
                logs.append(log)
    if res["next_block"] >= res["archive_height"]:
        break
    body["from_block"] = res["next_block"]
block = hex(res["archive_height"] - 1)  # read onchain state at the last block HyperSync returned
logs.sort(key=lambda l: (l["block_number"], l["log_index"]))

# 2. Latest Chainlink answers at the snapshot block, then the details (underlying, decimals) of each reserve the spokes listed.
def latest_answers(end):
    """Latest AnswerUpdated of each feed before block `end`, read with HyperSync. Looks back over a growing window
    of blocks until every feed has an answer. Returns {feed name: (price, updatedAt)}."""
    by_addr = {a.lower(): (n, d) for n, (a, d) in FEEDS.items()}
    found, window = {}, 200_000
    while len(found) < len(FEEDS):
        body = {"from_block": max(end - window, 0), "to_block": end,
                "logs": [{"address": list(by_addr), "topics": [[ANSWER_UPDATED]]}],
                "field_selection": {"log": ["block_number", "log_index", "address", "topic0", "topic1", "data"]}}
        latest = {}
        while True:
            res = post(HYPERSYNC, body, auth=True)
            for batch in res["data"]:
                for log in batch.get("logs") or []:
                    hit = by_addr.get(log["address"].lower())
                    if hit and log["topic0"] == ANSWER_UPDATED:
                        key = (log["block_number"], log["log_index"])
                        if hit[0] not in latest or key > latest[hit[0]][0]:
                            latest[hit[0]] = (key, int(log["topic1"], 16) / 10 ** hit[1], int(log["data"], 16))
            if res["next_block"] >= end:
                break
            body["from_block"] = res["next_block"]
        found = latest
        if end - window <= 0:
            break
        window *= 4
    return {n: (v[1], v[2]) for n, v in found.items()}


answers = latest_answers(int(block, 16) + 1)
reserves = {}
for log in logs:
    if log["topic0"] == ADD_RESERVE:
        spoke, rid = log["address"].lower(), int(log["topic1"], 16)
        r = call(spoke, "0x77778db3", rid, block)                     # getReserve(uint256)
        underlying, decimals = "0x" + format(word(r, 0), "040x"), word(r, 3)
        price = 1.0
        for name in PRICING[SPOKES[spoke][0]][rid]:  # a rate feed times a base feed, or one feed on its own
            price *= answers[name][0]
        oracle = word(call(SPOKES[spoke][1], "0xd45c35ff", rid, block), 0) / 1e8  # getReservePrice(uint256), check only
        reserves[(spoke, rid)] = {"symbol": symbol(underlying, block), "decimals": decimals, "price": price, "oracle": oracle,
                                  "supplied": 0, "borrowed": 0, "supply_shares": 0, "drawn_shares": 0,
                                  "supply_rate": None, "drawn_rate": None}

# 3. Replay the spokes. Aave v4 keeps positions in shares, so each reserve tracks supply shares and drawn (debt)
#    shares, and turns them into assets with the rate in its latest event: amount / shares in the last Supply or
#    Withdraw for supply, and in the last Borrow for debt. "supplied" and "borrowed" are plain principal sums.
daily = defaultdict(float)
for log in logs:
    if log["topic0"] == ADD_RESERVE:
        continue
    spoke = log["address"].lower()
    r = reserves[(spoke, int(log["topic1"], 16))]
    w = [word(log["data"], i) for i in range((len(log["data"]) - 2) // 64)]
    day = datetime.datetime.fromtimestamp(times[log["block_number"]], datetime.timezone.utc).date()
    if log["topic0"] == SUPPLY:
        r["supplied"] += w[1] / 10 ** r["decimals"]
        r["supply_shares"] += w[0]
        r["supply_rate"] = (w[1], w[0])
        daily[day] += w[1] / 10 ** r["decimals"] * r["price"]
    elif log["topic0"] == WITHDRAW:
        r["supplied"] -= w[1] / 10 ** r["decimals"]
        r["supply_shares"] -= w[0]
        r["supply_rate"] = (w[1], w[0])
        daily[day] -= w[1] / 10 ** r["decimals"] * r["price"]
    elif log["topic0"] == BORROW:
        r["borrowed"] += w[1] / 10 ** r["decimals"]
        r["drawn_shares"] += w[0]
        r["drawn_rate"] = (w[1], w[0])
    elif log["topic0"] in (REPAY, DEFICIT):
        r["drawn_shares"] -= w[0]
    elif log["topic0"] == LIQUIDATION:
        # topic1 is the collateral reserve, topic2 the debt reserve. Data: liquidator, receiveShares, debtRestored,
        # drawnSharesLiquidated, premiumDelta (3 words), collateralAmountRemoved, collateralSharesLiquidated, sharesToLiquidator
        reserves[(spoke, int(log["topic2"], 16))]["drawn_shares"] -= w[3]
        r["supply_shares"] -= w[8] - (w[9] if w[1] else 0)
        r["supplied"] -= (w[7] - (w[9] if w[1] else 0)) / 10 ** r["decimals"]
        daily[day] -= (w[7] - (w[9] if w[1] else 0)) / 10 ** r["decimals"] * r["price"]


def assets(shares, rate, decimals):
    return (shares * rate[0] // rate[1] if rate and rate[1] else 0) / 10 ** decimals


# 4. Print, and check each reserve against getReserveSuppliedAssets() and getReserveTotalDebt() over RPC.
#    The rebuilt figures use the share rate from each reserve's latest event, so the spoke's own figures sit slightly
#    higher by the interest earned since then. Debt from events is drawn debt only, without Aave v4's premium debt.
total, checks, by_symbol, oracle_total, price_checks = 0, [], defaultdict(float), 0, {}
for (spoke, rid), r in reserves.items():
    r["onchain"] = assets(r["supply_shares"], r["supply_rate"], r["decimals"])
    r["debt"] = assets(r["drawn_shares"], r["drawn_rate"], r["decimals"])
    total += r["onchain"] * r["price"]
    oracle_total += r["onchain"] * r["oracle"]
    if r["onchain"] * r["price"] >= 1e6:
        price_checks[r["symbol"]] = (r["price"], r["oracle"])
    by_symbol[r["symbol"]] += r["onchain"] * r["price"]
    if r["onchain"] or r["supplied"]:
        rpc = word(call(spoke, "0x2fd00527", rid, block), 0) / 10 ** r["decimals"]      # getReserveSuppliedAssets
        rpc_debt = word(call(spoke, "0x1cdc762c", rid, block), 0) / 10 ** r["decimals"]  # getReserveTotalDebt
        checks.append(f"  {SPOKES[spoke][0]:11} {r['symbol']:6} supplied {r['onchain']:>16,.2f}  RPC {rpc:>16,.2f}  gap {r['onchain'] - rpc:>10,.2f}"
                      f"  |  borrowed {r['debt']:>16,.2f}  RPC {rpc_debt:>16,.2f}  gap {r['debt'] - rpc_debt:>10,.2f}")

print(f"Supplied to Sentora's Aave v4 markets: ${total:,.0f} at Chainlink feed prices read with HyperSync")
for s, v in sorted(by_symbol.items(), key=lambda x: -x[1]):
    if v >= 1:
        print(f"  {s:6} ${v:>14,.0f}")
rl = reserves[("0x9ebf0c19bf7dfe859820cc09e846114b53814e52", 0)]
print(f"RLUSD borrowed in the RLUSD Yield market: ${rl['debt'] * rl['price']:,.0f} of ${rl['onchain'] * rl['price']:,.0f} supplied "
      f"({100 * rl['debt'] / rl['onchain']:.1f}% utilization)")
print("Supplied, day by day (USD at today's prices, principal)")
running = 0
for day in sorted(daily):
    running += daily[day]
    print(f"  {day}  {running:>16,.0f}")
print(f"Check (Aave oracle getReservePrice over RPC): the same supply is ${oracle_total:,.0f}, gap {100 * (total - oracle_total) / oracle_total:+.2f}%")
for sym, (p, o) in price_checks.items():
    print(f"  {sym:6} feed ${p:,.4f}  oracle ${o:,.4f}")
print(f"Check (RPC getReserveSuppliedAssets and getReserveTotalDebt at block {int(block, 16):,})")
print("\n".join(checks))
