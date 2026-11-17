# What sits in Sentora's curated markets on Aave v4, with Envio HyperSync.
# Reads every Supply, Withdraw and Borrow on Sentora's three Aave v4 spokes on Ethereum,
# rebuilds what has been supplied and borrowed, and checks it against the spokes' own state onchain.
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
ADD_RESERVE = "0xb2d3221c3db1eb0d586556ae23399acdfe3e52ff0fcd184c19069c730f9ca2e9"  # AddReserve(uint256,uint256,address)
TOPICS = [SUPPLY, WITHDRAW, BORROW, ADD_RESERVE]
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
    "field_selection": {"log": ["address", "topic0", "topic1", "topic3", "data", "block_number", "log_index"],
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

# 2. Reserve details (underlying, decimals) and current price for each reserve the spokes listed.
reserves = {}
for log in logs:
    if log["topic0"] == ADD_RESERVE:
        spoke, rid = log["address"].lower(), int(log["topic1"], 16)
        r = call(spoke, "0x77778db3", rid, block)                     # getReserve(uint256)
        underlying, decimals = "0x" + format(word(r, 0), "040x"), word(r, 3)
        price = word(call(SPOKES[spoke][1], "0xd45c35ff", rid, block), 0) / 1e8  # getReservePrice(uint256), 8 decimals
        reserves[(spoke, rid)] = {"symbol": symbol(underlying, block), "decimals": decimals, "price": price,
                                  "supplied": 0, "borrowed": 0}

# 3. Replay supplies, withdrawals and borrows. The amount is the second data word in each event.
daily = defaultdict(float)
for log in logs:
    if log["topic0"] == ADD_RESERVE:
        continue
    r = reserves[(log["address"].lower(), int(log["topic1"], 16))]
    amount = word(log["data"], 1) / 10 ** r["decimals"]
    day = datetime.datetime.fromtimestamp(times[log["block_number"]], datetime.timezone.utc).date()
    if log["topic0"] == SUPPLY:
        r["supplied"] += amount
        daily[day] += amount * r["price"]
    elif log["topic0"] == WITHDRAW:
        r["supplied"] -= amount
        daily[day] -= amount * r["price"]
    else:
        r["borrowed"] += amount

# 4. Print, and check each reserve against getReserveSuppliedAssets() onchain.
#    Onchain supply includes interest earned since each deposit, so it sits slightly above the replayed principal.
total, checks, by_symbol = 0, [], defaultdict(float)
for (spoke, rid), r in reserves.items():
    onchain = word(call(spoke, "0x2fd00527", rid, block), 0) / 10 ** r["decimals"]   # getReserveSuppliedAssets
    debt = word(call(spoke, "0x1cdc762c", rid, block), 0) / 10 ** r["decimals"]      # getReserveTotalDebt
    total += onchain * r["price"]
    by_symbol[r["symbol"]] += onchain * r["price"]
    r["onchain"], r["debt"] = onchain, debt
    if onchain or r["supplied"]:
        gap = onchain - r["supplied"]
        checks.append(f"  {SPOKES[spoke][0]:11} {r['symbol']:6} replayed {r['supplied']:>16,.2f}  onchain {onchain:>16,.2f}  interest {gap:>10,.2f}")

print(f"Supplied to Sentora's Aave v4 markets: ${total:,.0f}")
for s, v in sorted(by_symbol.items(), key=lambda x: -x[1]):
    if v >= 1:
        print(f"  {s:6} ${v:>14,.0f}")
rl = reserves[("0x9ebf0c19bf7dfe859820cc09e846114b53814e52", 0)]
print(f"RLUSD borrowed in the RLUSD Yield market: ${rl['debt'] * rl['price']:,.0f} of ${rl['onchain'] * rl['price']:,.0f} supplied "
      f"({100 * rl['debt'] / rl['onchain']:.1f}% utilization)")
print("Supplied, day by day (USD at today's prices)")
running = 0
for day in sorted(daily):
    running += daily[day]
    print(f"  {day}  {running:>16,.0f}")
print(f"Checks at block {int(block, 16):,}")
print("\n".join(checks))
