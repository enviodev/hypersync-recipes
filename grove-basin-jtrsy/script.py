# Grove Basin for JTRSY on Ethereum, with Envio HyperSync.
# Reads every event of Grove's JTRSY Basin: each swap of JTRSY (Janus Henderson Anemoy Treasury Fund, tokenized by
# Centrifuge) into USDC, and each redemption Basin then runs with the issuer in the background, with how long it took.
# Also reads Basin's current liquidity and maximum swap size with two eth_calls to a public Ethereum RPC.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

BASIN = "0xf08943f817e1f902debc884c7b19ea5764594ac9"  # JTRSY_GROVE_BASIN, docs.grove.finance/deployed-contracts
JTRSY = "0x8c213ee79581ff4984583c6a801e5263418c4b86"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
SWAP = "0xdba43ee9916cb156cc32a5d3406e87341e568126a46815294073ba25c9400246"  # Swap(assetIn,assetOut,sender,receiver,amountIn,amountOut,referralCode)
REDEEM_START = "0x59862feec418c14a7636196068d2a399c2d280c34b1934812c116231142fe69f"  # RedeemInitiated(redeemer,caller,amount)
REDEEM_DONE = "0x13eb5fe4e130586328212f8eee597341aaf6680fefba68a5441684311a41afe9"  # RedeemCompleted(redeemer,caller,amount)
RPC = "https://ethereum-rpc.publicnode.com"

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(url, body, headers=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", **(headers or {})})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def call(selector):
    return int(post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                          "params": [{"to": BASIN, "data": selector}, "latest"]})["result"], 16)


def words(data):
    data = data[2:]
    return [int(data[i:i + 64], 16) for i in range(0, len(data), 64)]


# 1. Every Swap, RedeemInitiated and RedeemCompleted event of the Basin, with block timestamps
body = {"from_block": 0, "logs": [{"address": [BASIN], "topics": [[SWAP, REDEEM_START, REDEEM_DONE]]}],
        "field_selection": {"log": ["block_number", "transaction_hash", "topic0", "topic1", "topic2", "data"],
                            "block": ["number", "timestamp"]}}
logs, stamps = [], {}
while True:
    res = post("https://eth.hypersync.xyz/query", body, {"Authorization": "Bearer " + TOKEN})
    for batch in res["data"]:
        logs += batch.get("logs") or []
        for b in batch.get("blocks") or []:
            stamps[b["number"]] = int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
    if res["next_block"] >= res["archive_height"]:
        break
    body["from_block"] = res["next_block"]
logs.sort(key=lambda l: (l["block_number"], l["transaction_hash"]))


def when(block):
    return datetime.fromtimestamp(stamps[block], timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# 2. Swaps: JTRSY in, USDC out, one transaction each
swaps = []
for l in logs:
    if l["topic0"] == SWAP and l["topic1"][-40:] == JTRSY[2:] and l["topic2"][-40:] == USDC[2:]:
        _, amount_in, amount_out, _ = words(l["data"])
        swaps.append((l["block_number"], l["transaction_hash"], amount_in / 1e6, amount_out / 1e6))
other = sum(1 for l in logs if l["topic0"] == SWAP) - len(swaps)
largest = max(swaps, key=lambda s: s[3])
print("Grove Basin for JTRSY on Ethereum")
print(f"  {len(swaps)} swaps of JTRSY into USDC, each in a single transaction ({other} swaps in any other direction)")
print(f"  {sum(s[2] for s in swaps):,.6f} JTRSY in, ${sum(s[3] for s in swaps):,.6f} USDC out")
print(f"  Largest: {largest[2]:,.6f} JTRSY into ${largest[3]:,.6f} USDC, {when(largest[0])}, tx {largest[1]}")
print(f"  Latest:  {swaps[-1][2]:,.6f} JTRSY into ${swaps[-1][3]:,.6f} USDC, {when(swaps[-1][0])}, tx {swaps[-1][1]}")

# 3. Redemptions Basin runs with the issuer afterwards, and how long each took to settle
print("Basin's own redemptions of the JTRSY it took in")
start = None
for l in logs:
    if l["topic0"] == REDEEM_START:
        start = l
    elif l["topic0"] == REDEEM_DONE and start:
        hours = (stamps[l["block_number"]] - stamps[start["block_number"]]) / 3600
        print(f"  {words(start['data'])[0] / 1e6:>12,.6f} JTRSY  requested {when(start['block_number'])}"
              f"  settled for ${words(l['data'])[0] / 1e6:,.6f} USDC after {hours:,.1f} hours ({hours / 24:.1f} days)")
        start = None
if start:
    print(f"  {words(start['data'])[0] / 1e6:>12,.6f} JTRSY  requested {when(start['block_number'])}  still settling")

# 4. Liquidity standing in the Basin right now, read onchain
print(f"Liquidity in the Basin now: ${call('0x01e1d114') / 1e18:,.2f}")  # totalAssets()
print(f"Largest single swap allowed: ${call('0x4f28cac2') / 1e18:,.0f}")  # maxSwapSize()
