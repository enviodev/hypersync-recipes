"""Ostium's biggest markets on Arbitrum, read straight from the chain with Envio HyperSync.

Reads every position opened on Ostium (MarketOpenExecuted and LimitOpenExecuted from the
TradingCallbacks contract) over the last 30 days, sizes each one as collateral x leverage,
and groups the total by pair and by Ostium's own asset groups (crypto, commodities, forex,
indices, stocks, etf). Pair names and groups are read from Ostium's PairsStorage contract.
It also reads open interest per pair from TradingStorage and values it at Ostium's live prices.

Run:
    export ENVIO_API_TOKEN=...   # free token: https://envio.dev/app/api-tokens
    python script.py              # 30 days ending at the last 00:00 UTC
    python script.py 2026-11-05   # 30 days ending at 00:00 UTC on that date
"""
import collections
import datetime as dt
import json
import os
import sys
import time
import urllib.request

HS = "https://arbitrum.hypersync.xyz"
RPC = "https://arb1.arbitrum.io/rpc"
PRICES = "https://builder.prod.bedrock.ostium.io/v1/prices"  # docs.ostium.com/developer/builder-api/get-prices
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

# Ostium mainnet contracts on Arbitrum One: docs.ostium.com/protocol/security/audits (contract table)
CALLBACKS = "0x7720fC8c8680bF4a1Af99d44c6c265a74e9742a9"       # TradingCallbacks, emits the open events
TRADING_STORAGE = "0xccd5891083a8acd2074690f65d3024e7d13d66e7"  # openInterest(pairIndex, 0 long / 1 short)
PAIRS_STORAGE = "0x260E349F643f12797fDc6f8c9d3df211D5577823"    # pairs(i), groups(g), pairsCount()

# Event signatures from github.com/0xOstium/smart-contracts-public, IOstiumTradingCallbacks.sol
# Trade = (collateral, openPrice, tp, sl, trader, leverage, pairIndex, index, buy, isDayTrade)
MARKET_OPEN = "0xc15478b6b68c100c76ab032fa5268715cb571da48263fd160aa4dc1afebb57ea"  # MarketOpenExecuted(uint256,Trade,uint256,uint256)
LIMIT_OPEN = "0x444c09c4da97dd4653c341eb77d39b9a5072fa7d719e556c7add607905ad8979"   # LimitOpenExecuted(uint256,uint256,Trade,uint256,uint256)
GROUP_LABEL = {"crypto": "Crypto", "commodities": "Commodities", "forex": "Forex",
               "indices": "Indices", "stocks": "Stocks", "etf": "ETFs"}


def post(url, body, headers=None):
    req = urllib.request.Request(url, json.dumps(body).encode(), {
        "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", **(headers or {})})
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(2 + 2 * attempt)
    sys.exit("Request kept failing: " + url)


def hs(body):
    return post(HS + "/query", body, {"Authorization": "Bearer " + TOKEN})


def call(to, data):
    return post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]})["result"][2:]


def word(n):
    return format(n, "064x")


def text(hex32):
    return bytes.fromhex(hex32).rstrip(b"\0").decode()


def block_at(ts):
    """First block at or after a unix timestamp, by binary search over HyperSync."""
    req = urllib.request.Request(HS + "/height", headers={"Authorization": "Bearer " + TOKEN})
    lo, hi = 0, json.load(urllib.request.urlopen(req, timeout=60))["height"]
    while lo < hi:
        mid = (lo + hi) // 2
        b = hs({"from_block": mid, "to_block": mid + 1, "blocks": [{}],
                "field_selection": {"block": ["timestamp"]}})["data"][0]["blocks"][0]["timestamp"]
        b = int(b, 16) if isinstance(b, str) else b
        lo, hi = (mid + 1, hi) if b < ts else (lo, mid)
    return lo


# 1. Pair names and asset groups, straight from Ostium's PairsStorage contract
count = int(call(PAIRS_STORAGE, "0xb81b2b71"), 16)  # pairsCount()
groups, pairs = {}, {}
for i in range(count):
    d = call(PAIRS_STORAGE, "0xc2b10883" + word(i))  # pairs(uint16)
    w = [d[k:k + 64] for k in range(0, 9 * 64, 64)]
    g = int(w[6], 16)
    if g not in groups:
        groups[g] = text(call(PAIRS_STORAGE, "0xe6587a86" + word(g))[:64])  # groups(uint8) -> name
    pairs[i] = (f"{text(w[0])}/{text(w[1])}", GROUP_LABEL.get(groups[g], groups[g]))

# Ostium's live prices and display names (the contract calls US500 "SPX" and US100 "NDX")
req = urllib.request.Request(PRICES, headers={"User-Agent": "Mozilla/5.0"})
feed = json.load(urllib.request.urlopen(req, timeout=60))["prices"]
mids = {p["from"] + "/" + p["to"]: p["mid"] for p in feed}
shown = {p["from"] + "/" + p["to"]: p["pair"].replace("-", "/") for p in feed}

# 2. Every position opened in the window, from the TradingCallbacks events
day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.datetime.now(dt.timezone.utc).date()
end = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())
start = end - 30 * 86400
a, b = block_at(start), block_at(end)
size, opens, traders = collections.Counter(), collections.Counter(), set()
while a < b:
    res = hs({"from_block": a, "to_block": b,
              "logs": [{"address": [CALLBACKS], "topics": [[MARKET_OPEN, LIMIT_OPEN]]}],
              "field_selection": {"log": ["address", "topic0", "data"]}})
    for batch in res["data"]:
        for log in batch.get("logs") or []:
            t0 = log["topic0"].lower()
            if log["address"].lower() != CALLBACKS.lower() or t0 not in (MARKET_OPEN, LIMIT_OPEN):
                continue
            d = log["data"][2:]
            w = [d[k:k + 64] for k in range(0, len(d), 64)]
            if t0 == LIMIT_OPEN:
                w = w[1:]  # skip limitIndex
            collateral, leverage, pair = int(w[0], 16) / 1e6, int(w[5], 16) / 100, int(w[6], 16)
            size[pair] += collateral * leverage
            opens[pair] += 1
            traders.add(w[4][-40:])
    a = res["next_block"]

total = sum(size.values())
by_group, trades_group = collections.Counter(), collections.Counter()
for p, v in size.items():
    by_group[pairs[p][1]] += v
    trades_group[pairs[p][1]] += opens[p]
n_trades = sum(opens.values())
print(f"Ostium on Arbitrum, positions opened {day - dt.timedelta(days=30)} to {day} (UTC, 30 days)")
print(f"  ${total / 1e6:,.1f}M opened across {sum(opens.values()):,} trades by {len(traders):,} traders\n")
print("By asset group         size   share of size   share of trades")
for g, v in by_group.most_common():
    print(f"  {g:12} ${v / 1e6:8,.1f}M  {100 * v / total:9.1f}%  {100 * trades_group[g] / n_trades:12.1f}%")
print(f"  Not crypto   ${(total - by_group['Crypto']) / 1e6:8,.1f}M  {100 * (1 - by_group['Crypto'] / total):9.1f}%  {100 * (1 - trades_group['Crypto'] / n_trades):12.1f}%\n")
print("Top 10 pairs")
for p, v in size.most_common(10):
    print(f"  {shown.get(pairs[p][0], pairs[p][0]):10} {pairs[p][1]:12} ${v / 1e6:8,.1f}M  {100 * v / total:5.1f}%  {opens[p]:>7,} trades")
top2 = size.most_common(2)
print(f"  Top 2 together: {100 * sum(v for _, v in top2) / total:.1f}%")

# 3. Open interest right now: long + short notional per pair from TradingStorage, at Ostium's live mid prices
oi, oi_group = collections.Counter(), collections.Counter()
for i, (name, group) in pairs.items():
    units = sum(int(call(TRADING_STORAGE, "0x7a523273" + word(i) + word(side)), 16) for side in (0, 1)) / 1e18
    if units == 0:
        continue
    base, quote = name.split("/")
    if quote == "USD":
        usd = units * mids[name]
    elif base == "USD":
        usd = units  # USD/JPY and friends: notional is already in dollars
    else:
        # e.g. NIK/JPY or FTSE/GBP: value in the local currency, converted with Ostium's own FX pair
        fx = 1 / mids["USD/" + quote] if "USD/" + quote in mids else mids[quote + "/USD"]
        usd = units * mids[name] * fx
    oi[name] += usd
    oi_group[group] += usd
oi_total = sum(oi.values())
print(f"\nOpen interest now ${oi_total / 1e6:,.1f}M")
for g, v in oi_group.most_common():
    print(f"  {g:12} ${v / 1e6:8,.1f}M  {100 * v / oi_total:5.1f}%")
print(f"  Not crypto   ${(oi_total - oi_group['Crypto']) / 1e6:8,.1f}M  {100 * (1 - oi_group['Crypto'] / oi_total):5.1f}%")
print("Top 5 pairs by open interest")
for name, v in oi.most_common(5):
    print(f"  {shown.get(name, name):10} ${v / 1e6:8,.1f}M  {100 * v / oi_total:5.1f}%")
