# SPCXc (Coinbase's tokenized SpaceX stock) on the Aave v4 tokenized stocks market on Base, with Envio HyperSync.
# Replays every SPCXc Transfer to count holders and rebuild supply, then replays every Supply, Withdraw, Borrow,
# Repay, LiquidationCall, ReportDeficit and SetUsingAsCollateral on the market's spoke to rebuild what is
# supplied and borrowed. Base's public RPC gives Aave oracle prices and labelled cross-checks of the spoke's state.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

HYPERSYNC = "https://base.hypersync.xyz/query"
RPC = "https://mainnet.base.org"
# Market addresses from https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Base.sol
HUB = "0xa4d5947eb727a052bae69c593ffc84247ec9864e"     # EQUITIES_HUB
SPOKE = "0x17905db0e4a3514467539956c084180616ae7b8d"   # MAG7_SPOKE
ORACLE = "0xabaf048fd7675ea34a84332371ffd5d55e322a47"  # MAG7_SPOKE_ORACLE
# SPCXc, listed by Coinbase at https://api.coinbase.com/v1/tokenized-stocks and in the address book above
SPCXC = "0xb2000000000000000000007b9fcbd005511acbd5"
USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
# Event topics, keccak of the signatures in the verified Spoke ABI (Sourcify) and aave/aave-v4 IHub.sol
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ADD_ASSET = "0x92fb402b777f3710166f15b30098f41042b439850df67d0195196d125458e7b3"   # Hub AddAsset(uint256,address,uint8)
ADD_RESERVE = "0xb2d3221c3db1eb0d586556ae23399acdfe3e52ff0fcd184c19069c730f9ca2e9"  # Spoke AddReserve(uint256,uint256,address)
SUPPLY = "0xd986db228cb1fe8392c5f45ff5f2c639b7db6cbd9ca7d1fe70b2de90c2c8c961"
WITHDRAW = "0xfe7813e2866053d5c3938554e517b554fce6666a6561bed9eaa7419b29fa9b68"
BORROW = "0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"
REPAY = "0xd765a0263e8a360da8dd4fdb8c0dc5553adec12a96f29a462cdb45e5bea407dd"
LIQUIDATION = "0x2a1f12d996f530f89d8038aa293f9fde81cac44b6dfd6225e3358d09b78a4a37"  # LiquidationCall(uint256,uint256,address,address,bool,uint256,uint256,(int256,int256,uint256),uint256,uint256,uint256)
DEFICIT = "0x59932f333b3a5e3fec86e662babe8dd767529ed207420e7468bd220cdfb3f076"      # ReportDeficit(uint256,address,uint256,(int256,int256,uint256))
COLLATERAL = "0x4763df430bc5274807f8ab4ce0734e7898513638418d6eec0c5285ef85f7f51f"   # SetUsingAsCollateral(uint256,address,address,bool)

ANSWER_UPDATED = "0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f"  # AnswerUpdated(int256 indexed current, uint256 indexed roundId, uint256 updatedAt)
# Chainlink aggregators (8 decimals) behind the market's oracle, by reserve id. Found with the oracle's
# getReserveSource(reserveId), which returns a price feed proxy, then the proxy's aggregator().
FEEDS = {
    0: ("AAPL", "0xc37B6F754e90D4Cca1f533F5a08f7d532b3d0d9D"),
    1: ("AMZN", "0x4816cb7EE43eE12C0BC9D3C597246f34D5CFdb7C"),
    2: ("GOOGL", "0x6bF33b7855eB8047dDe206D9F6321D7d02CfB308"),
    3: ("META", "0xA7155928bEE40052EFb3094a046c5498202FD3EE"),
    4: ("MSFT", "0xD72B34be6c2180Ad0d28dbb415AEfdE8a55F3eD3"),
    5: ("NVDA", "0xF72B1eB5932800F3d2a5EeC5f99e6cD586479675"),
    6: ("TSLA", "0x0288234d9311C33BE6c3a34b051bff8A799dAA82"),
    7: ("USDC", "0x68bE4C50235205Ede361ac8244B1ee221CDDA5E2"),
    8: ("SPCX", "0xa994B7fC3123AE0EF4EE53ab5e3545f2639187a7"),
}

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def request(url, body, auth=False):
    headers = {"Content-Type": "application/json", "User-Agent": "curl/8"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers)
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def logs(selections):
    body = {"from_block": 0, "logs": selections,
            "field_selection": {"block": ["number", "timestamp"],
                                "log": ["address", "block_number", "log_index", "topic0", "topic1", "topic2", "topic3", "data"]}}
    rows, times = [], {}
    while True:
        res = request(HYPERSYNC, body, auth=True)
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                times[b["number"]] = int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
            rows += batch.get("logs") or []
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]
    rows.sort(key=lambda l: (l["block_number"], l["log_index"]))
    return rows, times, res["archive_height"] - 1


def latest_answers(feeds, end):
    """Latest AnswerUpdated of each feed before block `end`, read with HyperSync. Looks back over a growing window
    of blocks until every feed has an answer. Returns {reserve id: (price in USD, updatedAt)}."""
    by_addr = {a.lower(): rid for rid, (_n, a) in feeds.items()}
    found, window = {}, 400_000
    while len(found) < len(feeds):
        body = {"from_block": max(end - window, 0), "to_block": end,
                "logs": [{"address": list(by_addr), "topics": [[ANSWER_UPDATED]]}],
                "field_selection": {"log": ["block_number", "log_index", "address", "topic0", "topic1", "data"]}}
        latest = {}
        while True:
            res = request(HYPERSYNC, body, auth=True)
            for batch in res["data"]:
                for log in batch.get("logs") or []:
                    rid = by_addr.get(log["address"].lower())
                    if rid is not None and log["topic0"] == ANSWER_UPDATED:
                        key = (log["block_number"], log["log_index"])
                        if rid not in latest or key > latest[rid][0]:
                            latest[rid] = (key, int(log["topic1"], 16) / 1e8, int(log["data"], 16))
            if res["next_block"] >= end:
                break
            body["from_block"] = res["next_block"]
        found = latest
        if end - window <= 0:
            break
        window *= 4
    return {rid: (v[1], v[2]) for rid, v in found.items()}


def words(data):
    data = data[2:]
    return [int(data[i:i + 64], 16) for i in range(0, len(data), 64)]


def addr(topic):
    return "0x" + topic[-40:]


def call(to, selector, *args, block="latest"):
    data = selector + "".join((a[2:].rjust(64, "0") if isinstance(a, str) else format(a, "064x")) for a in args)
    res = request(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, block]})
    if "result" not in res:
        sys.exit(f"eth_call failed: {res}")
    return words(res["result"])


def when(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%d %b %Y %H:%M UTC")


# 1. SPCXc token: replay every Transfer since deployment
transfers, _, head = logs([{"address": [SPCXC], "topics": [[TRANSFER]]}])
block = hex(head)  # read all state at the last block HyperSync returned, so events and state line up
balances, minted, burned = defaultdict(int), 0, 0
for log in transfers:
    src, dst, amount = addr(log["topic1"]), addr(log["topic2"]), words(log["data"])[0]
    if src == "0x" + "0" * 40:
        minted += amount
    else:
        balances[src] -= amount
    if dst == "0x" + "0" * 40:
        burned += amount
    else:
        balances[dst] += amount
decimals = call(SPCXC, "0x313ce567", block=block)[0]
supply = call(SPCXC, "0x18160ddd", block=block)[0]
multiplier = call(SPCXC, "0xa60bf13d", block=block)[0]  # uiMultiplier(), 1e18 means displayed units equal raw units
holders = sum(1 for v in balances.values() if v > 0)
print(f"SPCXc {SPCXC} at block {head:,}")
print(f"  decimals {decimals}, UI multiplier {multiplier / 1e18:g}")
print(f"  supply, minted - burned (HyperSync Transfers)  {(minted - burned) / 10 ** decimals:,.8f}")
print(f"  Check (RPC totalSupply()):                     {supply / 10 ** decimals:,.8f}  "
      f"{'matches' if minted - burned == supply else 'DOES NOT MATCH'}")
supply = minted - burned
print(f"  holders with a nonzero balance: {holders:,} (from {len(transfers):,} Transfer events)")

# 2. The market: assets on the Hub, reserves on the spoke, and every user action on the spoke
rows, times, _ = logs([{"address": [HUB], "topics": [[ADD_ASSET]]},
                       {"address": [SPOKE], "topics": [[ADD_RESERVE, SUPPLY, WITHDRAW, BORROW, REPAY, LIQUIDATION, DEFICIT, COLLATERAL]]}])
rows = [l for l in rows if l["block_number"] <= head]
underlying, reserves = {}, {}
for log in rows:
    if log["address"].lower() == HUB and log["topic0"] == ADD_ASSET:
        underlying[int(log["topic1"], 16)] = (addr(log["topic2"]), words(log["data"])[0])
    elif log["address"].lower() == SPOKE and log["topic0"] == ADD_RESERVE and addr(log["topic3"]) == HUB:
        reserves[int(log["topic1"], 16)] = (int(log["topic2"], 16), log["block_number"])


def symbol(token):
    res = request(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": token, "data": "0x95d89b41"}, block]})
    data = bytes.fromhex(res["result"][2:])
    length = int.from_bytes(data[32:64], "big")
    return data[64:64 + length].decode()


info = {}
for rid, (aid, listed) in sorted(reserves.items()):
    token, dec = underlying[aid]
    info[rid] = {"token": token, "symbol": symbol(token), "dec": dec, "listed": listed}
spcxc_rid = next(r for r, v in info.items() if v["token"] == SPCXC)
usdc_rid = next(r for r, v in info.items() if v["token"] == USDC)
listed_at = info[spcxc_rid]["listed"]

# Replay the spoke. Aave v4 tracks positions in shares, so the script keeps supply shares and drawn (debt) shares
# per reserve and per user, and turns shares into assets with the rate in the reserve's latest event
# (amount / shares in the last Supply or Withdraw for supply, the last Borrow for debt).
supply_shares, drawn_shares = defaultdict(int), defaultdict(int)
supply_rate, drawn_rate = {}, {}
user_supply, user_drawn, user_collateral = defaultdict(int), defaultdict(int), {}
for log in rows:
    if log["address"].lower() != SPOKE or log["topic0"] in (ADD_RESERVE,):
        continue
    t, w, rid = log["topic0"], words(log["data"]), int(log["topic1"], 16)
    if t == SUPPLY:
        supply_shares[rid] += w[0]
        supply_rate[rid] = (w[1], w[0])
        user_supply[rid, addr(log["topic3"])] += w[0]
    elif t == WITHDRAW:
        supply_shares[rid] -= w[0]
        supply_rate[rid] = (w[1], w[0])
        user_supply[rid, addr(log["topic3"])] -= w[0]
    elif t == BORROW:
        drawn_shares[rid] += w[0]
        drawn_rate[rid] = (w[1], w[0])
        user_drawn[rid, addr(log["topic3"])] += w[0]
    elif t == REPAY:
        drawn_shares[rid] -= w[0]
        user_drawn[rid, addr(log["topic3"])] -= w[0]
    elif t == DEFICIT:
        drawn_shares[rid] -= w[0]
        user_drawn[rid, addr(log["topic2"])] -= w[0]
    elif t == LIQUIDATION:
        # data: liquidator, receiveShares, debtRestored, drawnSharesLiquidated, premiumDelta (3 words),
        #       collateralAmountRemoved, collateralSharesLiquidated, collateralSharesToLiquidator
        debt_rid, user, liquidator = int(log["topic2"], 16), addr(log["topic3"]), "0x" + format(w[0], "040x")
        drawn_shares[debt_rid] -= w[3]
        user_drawn[debt_rid, user] -= w[3]
        supply_shares[rid] -= w[8]
        user_supply[rid, user] -= w[8]
        if w[1]:  # the liquidator took supply shares, which stay in the reserve
            supply_shares[rid] += w[9]
            user_supply[rid, liquidator] += w[9]
    elif t == COLLATERAL:
        user_collateral[rid, addr(log["topic3"])] = bool(w[0])


def assets(shares, rate):
    return shares * rate[0] // rate[1] if rate and rate[1] else 0


oracle_dec = call(ORACLE, "0x313ce567", block=block)[0]
answers = latest_answers(FEEDS, head + 1)
print(f"\nAave v4 tokenized stocks market on Base (Hub {HUB}, spoke {SPOKE}), rebuilt from spoke events")
print(f"  {'reserve':8}{'asset':8}{'supplied now':>20}{'feed price':>14}{'value':>16}{'borrowed now':>18}")
collateral_usd, checks, oracle_usd, price_checks = 0, [], 0, []
for rid, v in sorted(info.items()):
    supplied = assets(supply_shares[rid], supply_rate.get(rid)) / 10 ** v["dec"]
    debt = assets(drawn_shares[rid], drawn_rate.get(rid)) / 10 ** v["dec"]
    price = answers[rid][0]                                                       # latest Chainlink answer, from HyperSync logs
    oracle_price = call(ORACLE, "0xd45c35ff", rid, block=block)[0] / 10 ** oracle_dec  # getReservePrice, check only
    v.update(supplied=supplied, debt=debt, price=price)
    if rid != usdc_rid:
        collateral_usd += supplied * price
        oracle_usd += supplied * oracle_price
        price_checks.append(f"  {v['symbol']:8}feed ${price:>10,.4f}  oracle ${oracle_price:>10,.4f}  (feed updated {when(answers[rid][1])})")
    print(f"  {rid:<8}{v['symbol']:8}{supplied:>20,.4f}{price:>14,.4f}{supplied * price:>16,.0f}{debt:>18,.2f}")
    rpc_supplied = call(SPOKE, "0x2fd00527", rid, block=block)[0] / 10 ** v["dec"]   # getReserveSuppliedAssets
    rpc_debt = call(SPOKE, "0x1cdc762c", rid, block=block)[0] / 10 ** v["dec"]       # getReserveTotalDebt
    checks.append(f"  {rid:<8}{v['symbol']:8}{rpc_supplied:>20,.4f} (gap {supplied - rpc_supplied:,.4f}){rpc_debt:>18,.2f} (gap {debt - rpc_debt:,.2f})")
stocks = [v["symbol"] for r, v in sorted(info.items()) if r != usdc_rid]
print(f"  {len(stocks)} stocks listed: {', '.join(stocks)}")
print(f"  stock collateral supplied: ${collateral_usd:,.0f} at Chainlink feed prices read with HyperSync")
print(f"  USDC supplied: {info[usdc_rid]['supplied']:,.0f}, USDC borrowed (drawn debt, without premium): {info[usdc_rid]['debt']:,.0f}")
print("  Check (RPC getReserveSuppliedAssets, getReserveTotalDebt at the same block)")
print("\n".join(checks))
print(f"  Check (Aave oracle getReservePrice over RPC): stock collateral ${oracle_usd:,.0f}, gap {100 * (collateral_usd - oracle_usd) / oracle_usd:+.2f}%")
print("\n".join(price_checks))

# 3. SPCXc since it was listed
dec = info[spcxc_rid]["dec"]
supplies = [l for l in rows if l["topic0"] == SUPPLY and int(l["topic1"], 16) == spcxc_rid]
withdraws = [l for l in rows if l["topic0"] == WITHDRAW and int(l["topic1"], 16) == spcxc_rid]
depositors = {addr(l["topic3"]) for l in supplies}
in_amt = sum(words(l["data"])[1] for l in supplies)
out_amt = sum(words(l["data"])[1] for l in withdraws)
print(f"\nSPCXc on the market, reserve {spcxc_rid}, listed {when(times[listed_at])} (block {listed_at:,})")
print(f"  first supply {when(times[supplies[0]['block_number']])}" if supplies else "  no supplies yet")
print(f"  {len(supplies)} Supply events from {len(depositors)} addresses, {in_amt / 10 ** dec:,.4f} SPCXc in")
print(f"  {len(withdraws)} Withdraw events, {out_amt / 10 ** dec:,.4f} SPCXc out, net {(in_amt - out_amt) / 10 ** dec:,.4f}")
print(f"  supplied now: {info[spcxc_rid]['supplied']:,.4f} SPCXc = "
      f"${info[spcxc_rid]['supplied'] * info[spcxc_rid]['price']:,.0f} at ${info[spcxc_rid]['price']:,.4f}")
print(f"  share of all SPCXc: {info[spcxc_rid]['supplied'] / (supply / 10 ** dec):.1%}")

# USDC borrowed by addresses that have supplied SPCXc. They may hold other stocks as collateral too.
borrows_since = [l for l in rows if l["topic0"] == BORROW and int(l["topic1"], 16) == usdc_rid and l["block_number"] >= listed_at]
by_spcxc = [l for l in borrows_since if addr(l["topic3"]) in depositors]
holding = [user for user in depositors if user_supply[spcxc_rid, user] > 0]
collateral_on = sum(1 for user in holding if user_collateral.get((spcxc_rid, user)))
debt_now = sum(assets(user_drawn[usdc_rid, user], drawn_rate.get(usdc_rid)) for user in depositors)
u = 10 ** info[usdc_rid]["dec"]
print(f"  {len(holding)} addresses still supply SPCXc, {collateral_on} with it enabled as collateral")
print(f"  USDC owed now by SPCXc suppliers (drawn debt): {debt_now / u:,.2f}")
print(f"  USDC Borrow events since listing: {len(borrows_since)} market-wide ({sum(words(l['data'])[1] for l in borrows_since) / u:,.0f} USDC), "
      f"{len(by_spcxc)} by SPCXc suppliers ({sum(words(l['data'])[1] for l in by_spcxc) / u:,.0f} USDC)")
rpc_debt_now = sum(call(SPOKE, "0x9b7172a6", usdc_rid, user, block=block)[0] for user in depositors)  # getUserTotalDebt
print(f"  Check (RPC getUserTotalDebt, summed): {rpc_debt_now / u:,.2f}, gap {(debt_now - rpc_debt_now) / u:,.2f}")

# 4. Cross-check against Coinbase's tokenized stocks API
listing, page = None, None
while listing is None:
    res = request("https://api.coinbase.com/v1/tokenized-stocks" + (f"?page_token={page}" if page else ""), None)
    listing = next((t for t in res["tokens"] if t["contract_address"].lower() == SPCXC), None)
    page = res.get("next_page_token")
    if not page:
        break
if listing:
    print(f"\nCoinbase API: {listing['symbol']} decimals {listing['decimals']}, total_supply {listing.get('total_supply')}, "
          f"nav_price {listing.get('nav_price')} at {listing.get('nav_price_updated_at')}")
