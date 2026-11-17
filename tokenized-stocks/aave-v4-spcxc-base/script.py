# SPCXc (Coinbase's tokenized SpaceX stock) on the Aave v4 tokenized stocks market on Base, with Envio HyperSync.
# Replays every SPCXc Transfer to count holders, reads every Supply, Withdraw, Borrow and Repay on the
# market's spoke, then reads the market's live state and Aave oracle prices with eth_call.
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
print(f"  totalSupply (eth_call)       {supply / 10 ** decimals:,.8f}")
print(f"  minted - burned (Transfers)  {(minted - burned) / 10 ** decimals:,.8f}  "
      f"{'matches' if minted - burned == supply else 'DOES NOT MATCH'}")
print(f"  holders with a nonzero balance: {holders:,} (from {len(transfers):,} Transfer events)")

# 2. The market: assets on the Hub, reserves on the spoke, and every user action on the spoke
rows, times, _ = logs([{"address": [HUB], "topics": [[ADD_ASSET]]},
                       {"address": [SPOKE], "topics": [[ADD_RESERVE, SUPPLY, WITHDRAW, BORROW, REPAY]]}])
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

oracle_dec = call(ORACLE, "0x313ce567", block=block)[0]
print(f"\nAave v4 tokenized stocks market on Base (Hub {HUB}, spoke {SPOKE})")
print(f"  {'reserve':8}{'asset':8}{'supplied now':>20}{'oracle price':>14}{'value':>16}{'borrowed now':>18}")
collateral_usd = 0
for rid, v in sorted(info.items()):
    supplied = call(SPOKE, "0x2fd00527", rid, block=block)[0] / 10 ** v["dec"]   # getReserveSuppliedAssets
    debt = call(SPOKE, "0x1cdc762c", rid, block=block)[0] / 10 ** v["dec"]       # getReserveTotalDebt
    price = call(ORACLE, "0xd45c35ff", rid, block=block)[0] / 10 ** oracle_dec    # getReservePrice
    v.update(supplied=supplied, debt=debt, price=price)
    if rid != usdc_rid:
        collateral_usd += supplied * price
    print(f"  {rid:<8}{v['symbol']:8}{supplied:>20,.4f}{price:>14,.4f}{supplied * price:>16,.0f}{debt:>18,.2f}")
stocks = [v["symbol"] for r, v in sorted(info.items()) if r != usdc_rid]
print(f"  {len(stocks)} stocks listed: {', '.join(stocks)}")
print(f"  stock collateral supplied: ${collateral_usd:,.0f} at Aave oracle prices")
print(f"  USDC supplied: {info[usdc_rid]['supplied']:,.0f}, USDC borrowed (debt incl. interest): {info[usdc_rid]['debt']:,.0f}")

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
print(f"  supplied now (eth_call): {info[spcxc_rid]['supplied']:,.4f} SPCXc = "
      f"${info[spcxc_rid]['supplied'] * info[spcxc_rid]['price']:,.0f} at ${info[spcxc_rid]['price']:,.4f}")
print(f"  share of all SPCXc: {info[spcxc_rid]['supplied'] / (supply / 10 ** dec):.1%}")

# USDC borrowed by addresses that have supplied SPCXc. They may hold other stocks as collateral too.
borrows_since = [l for l in rows if l["topic0"] == BORROW and int(l["topic1"], 16) == usdc_rid and l["block_number"] >= listed_at]
by_spcxc = [l for l in borrows_since if addr(l["topic3"]) in depositors]
debt_now, collateral_on, holding = 0, 0, 0
for user in depositors:
    if call(SPOKE, "0xf1568a89", spcxc_rid, user, block=block)[0] > 0:          # getUserSuppliedAssets
        holding += 1
        enabled, _ = call(SPOKE, "0xa2a522f1", spcxc_rid, user, block=block)   # getUserReserveStatus
        collateral_on += enabled
    debt_now += call(SPOKE, "0x9b7172a6", usdc_rid, user, block=block)[0]      # getUserTotalDebt
u = 10 ** info[usdc_rid]["dec"]
print(f"  {holding} addresses still supply SPCXc, {collateral_on} with it enabled as collateral")
print(f"  USDC owed now by SPCXc suppliers: {debt_now / u:,.2f}")
print(f"  USDC Borrow events since listing: {len(borrows_since)} market-wide ({sum(words(l['data'])[1] for l in borrows_since) / u:,.0f} USDC), "
      f"{len(by_spcxc)} by SPCXc suppliers ({sum(words(l['data'])[1] for l in by_spcxc) / u:,.0f} USDC)")

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
