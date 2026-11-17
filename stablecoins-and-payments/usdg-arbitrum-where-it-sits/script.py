"""Where USDG sits on Arbitrum One.

Reads every Transfer event of Paxos Global Dollar (USDG) on Arbitrum One with Envio HyperSync,
rebuilds every holder's balance and the total supply, then groups the balances by where the
USDG sits: GMX markets, Morpho, other contracts and plain wallets.

The second source is a public Arbitrum RPC (totalSupply and balanceOf at the same block).
"""
import collections, datetime, json, os, sys, time, urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN")
HS = "https://arbitrum.hypersync.xyz"
RPC = os.environ.get("ARBITRUM_RPC", "https://arb1.arbitrum.io/rpc")          # balance checks at a fixed block
CODE_RPC = os.environ.get("ARBITRUM_CODE_RPC", "https://arbitrum-one-rpc.publicnode.com")  # one eth_getCode per holder
# USDG on Arbitrum One, from https://docs.paxos.com/guides/stablecoin/usdg/mainnet
USDG = "0x004b506865409877c9fa29bfb1eba929984b9bbc"
# Morpho on Arbitrum One, from https://docs.morpho.org/get-started/resources/addresses
MORPHO = "0x6c247b1f6182318877311737bac0844baa518f5e"
# GMX markets that hold USDG, from GMX's own API (https://arbitrum-api.gmxinfra.io/markets)
GMX_MARKETS = {
    "0xe57b97f2f83f39e74ec83f3e039fd370884784ff": "BTC/USD",
    "0x6f095f58e9eb2c583a1828202712c03962491d7e": "ETH/USD",
    "0x2ceeafca180b07c9d1d2f1086f8f59aafd282832": "ZEC/USD",
    "0x54bc430a788dffd4ae35e751e10899489f5a953f": "NEAR/USD",
    "0xc9ed746d613eefc0f196658f6030e90482593004": "XRP/USD",
    "0x408e8e83d4b8ac4bdeffdf896b49268a5fe5ef44": "USDC/USDG swap",
    "0x162c091263fbb3dfaf1d55dcc979533eb341da5f": "HYPE/USD",
    "0xff63b0f938772e2b4ffd1a1b340afe49616c95f2": "SOL/USD",
}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64
DECIMALS = 6


def post(url, body, auth=True):
    headers = {"Content-Type": "application/json", "User-Agent": "hypersync-example"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    for attempt in range(12):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise SystemExit("request failed: " + url)


def refresh_gmx_markets():
    """Pick up any USDG market GMX has listed since this script was written."""
    try:
        req = urllib.request.Request("https://arbitrum-api.gmxinfra.io/markets", headers={"User-Agent": "hypersync-example"})
        for m in json.load(urllib.request.urlopen(req, timeout=30))["markets"]:
            if USDG in (m["longToken"].lower(), m["shortToken"].lower()):
                GMX_MARKETS.setdefault(m["marketToken"].lower(), m["name"].split(" [")[0])
    except Exception:
        pass  # the list above still works


# 1. Every USDG Transfer on Arbitrum One, from HyperSync
logs, block_ts = [], {}
body = {"from_block": 0,
        "logs": [{"address": [USDG], "topics": [[TRANSFER]]}],
        "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data", "block_number", "log_index"],
                            "block": ["number", "timestamp"]}}
while True:
    r = post(HS + "/query", body)
    for batch in r["data"]:
        for b in batch.get("blocks") or []:
            ts = b["timestamp"]
            block_ts[b["number"]] = int(ts, 16) if isinstance(ts, str) else ts
        for log in batch.get("logs") or []:
            # default join only; keep exactly the token and event we asked for
            if log["address"].lower() == USDG and log["topic0"] == TRANSFER and log.get("topic2"):
                logs.append(log)
    if r["next_block"] >= r["archive_height"]:
        break
    body["from_block"] = r["next_block"]
logs.sort(key=lambda l: (l["block_number"], l["log_index"]))
last_block = logs[-1]["block_number"]
refresh_gmx_markets()

# 2. Rebuild balances and supply as integers, and keep a daily series
day = lambda ts: datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
bal = collections.Counter()
supply = gmx = morpho = 0
daily = collections.OrderedDict()
for log in logs:
    v = int(log["data"], 16)
    frm, to = "0x" + log["topic1"][-40:], "0x" + log["topic2"][-40:]
    if log["topic1"] == ZERO:
        supply += v
    else:
        bal[frm] -= v
        gmx -= v if frm in GMX_MARKETS else 0
        morpho -= v if frm == MORPHO else 0
    if log["topic2"] == ZERO:
        supply -= v
    else:
        bal[to] += v
        gmx += v if to in GMX_MARKETS else 0
        morpho += v if to == MORPHO else 0
    daily[day(block_ts[log["block_number"]])] = {"supply": supply, "gmx": gmx, "morpho": morpho}

# 3. Split what's left into other contracts and wallets (one eth_getCode per holder with $1 or more)
unit = 10 ** DECIMALS
holders = [a for a, b in bal.items() if b >= unit]
other_contracts = wallets = 0
for a in holders:
    if a in GMX_MARKETS or a == MORPHO:
        continue
    code = post(CODE_RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_getCode", "params": [a, "latest"]}, auth=False)["result"]
    if len(code) > 2 and not code.startswith("0xef0100"):  # 0xef0100 is a wallet with an EIP-7702 delegation
        other_contracts += bal[a]
    else:
        wallets += bal[a]

m = lambda v: f"${v / unit / 1e6:,.2f}M"
pct = lambda v: f"{100 * v / supply:.1f}%"
when = datetime.datetime.fromtimestamp(block_ts[last_block], datetime.timezone.utc)
print(f"USDG on Arbitrum One, {len(logs):,} transfers, up to block {last_block:,} ({when:%d %b %Y %H:%M} UTC)")
print(f"Supply            {m(supply)}")
print(f"In GMX markets    {m(gmx)}  {pct(gmx)}")
for a, name in sorted(GMX_MARKETS.items(), key=lambda x: -bal[x[0]]):
    print(f"    {name:<16}{m(bal[a])}")
print(f"In Morpho         {m(morpho)}  {pct(morpho)}")
print(f"Other contracts   {m(other_contracts)}  {pct(other_contracts)}")
print(f"Wallets           {m(wallets)}  {pct(wallets)}")

# 4. Check against the RPC at the same block
def call(to, data):
    out = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                     "params": [{"to": to, "data": data}, hex(last_block)]}, auth=False)
    return int(out["result"], 16)

rpc_supply = call(USDG, "0x18160ddd")
rpc_gmx = sum(call(USDG, "0x70a08231" + a[2:].rjust(64, "0")) for a in GMX_MARKETS)
rpc_morpho = call(USDG, "0x70a08231" + MORPHO[2:].rjust(64, "0"))
print("\nCheck against RPC at the same block (the comparison, not the source)")
print(f"  totalSupply     {m(rpc_supply)}  {'match' if rpc_supply == supply else 'DIFFERENT'}")
print(f"  GMX markets     {m(rpc_gmx)}  {'match' if rpc_gmx == gmx else 'DIFFERENT'}")
print(f"  Morpho          {m(rpc_morpho)}  {'match' if rpc_morpho == morpho else 'DIFFERENT'}")

json.dump({"block": last_block, "time": when.isoformat(), "supply": supply, "gmx": gmx, "morpho": morpho,
           "other_contracts": other_contracts, "wallets": wallets,
           "gmx_markets": {GMX_MARKETS[a]: bal[a] for a in GMX_MARKETS}, "daily": daily},
          open("usdg_arbitrum.json", "w"), indent=1)
