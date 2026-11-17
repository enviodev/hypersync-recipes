# What sits in Aave v3 on Monad, by asset, with Envio HyperSync.
# Sums every transfer of each reserve token into and out of its Aave aToken, which is what the pool holds (supplied minus borrowed).
# Prices come from Aave's own oracle with one RPC call per asset. Python 3 standard library only. Set ENVIO_API_TOKEN first.
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

URL = "https://monad.hypersync.xyz"
RPC = "https://rpc.monad.xyz"
# Addresses from https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol
ORACLE = "0x0c02b2c2038066c10eab8fe1d5cdb73d5a78a1bf"
RESERVES = {  # symbol: (underlying, aToken, decimals, counts as a dollar token)
    "USDT0": ("0xe7cd86e13ac4309349f30b3435a9d337750fc82d", "0x9531e6bc99d7f7f0596ed7ba5b846ba9eb60468c", 6, True),
    "USDC": ("0x754704bc059f8c67012fed69bc8a327a5aafb603", "0x35a73bacb179d3740395a3cecc87ff2e581d6042", 6, True),
    "USDe": ("0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34", "0x37cabe3edd86165886877cc8b6be10269f21893d", 18, True),
    "mUSD": ("0xaca92e438df0b2401ff60da7e4337b687a2435da", "0xdbb2e1b6bc94328df2662a1796ab6a23fcde3199", 6, True),
    "AUSD": ("0x00000000efe302beaa2b3e6e1b18d08d69a9012a", "0xdebfedf35faed5d1664e553545e144c02227a2ec", 6, True),
    "WETH": ("0xee8c0e9f1bffb4eb878d8f15f368a02a35481242", "0x4377b53aaa8b8e3ff7aa2843832caf004f5cb8b6", 18, False),
    "cbBTC": ("0xd18b7ec58cdf4876f6afebd3ed1730e4ce10414b", "0x1f5e388861a32226c716e922ce748a6fee5e8e57", 8, False),
    "wstETH": ("0x10aeaf63194db8d453d4d85a06e5efe1dd0b5417", "0xc31e3a273a93d238ce49b053f801e8f385375df7", 18, False),
    "weETH": ("0xa3d68b74bf0528fdd07263c60d6488749044914b", "0x4fae5e2d191e012f503de53023b0710f554fcff0", 18, False),
    "syrupUSDC": ("0xab6e5a0c3799d020c790d34f7b2c02639e238af7", "0xbc2a1fa0069e59e2552ab40889520c7b0d413d9b", 6, True),
    "sUSDe": ("0x211cc4dd073734da055fbf44a2b4667d5e5fe5d2", "0xcd11405d4a15a825b46254c42f5b5cd8c2edae09", 18, True),
    "GHO": ("0xfc421ad3c883bf9e7c4f42de845c4e4405799e73", "0x4586face17b0e3d4d51ecabb4b4ebc2354b61b0d", 18, True),
    "PT-AUSD-8OCT2026": ("0x9fc74f8ed616b5baf52a170caa97d6d3898602d1", "0xb93ce4eb85eba317f954dadcbe112ce6c3af9ae4", 6, True),
    "PT-AUSD-17DEC2026": ("0x8b562578b2f9aa8c14ccda3c5d6cbcead3b06a57", "0x8f8d143f1fce0a57a6e80d8df7f7288703b2eb7e", 6, True),
}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(path, body=None):
    req = urllib.request.Request(URL + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def price(asset):
    # AaveOracle.getAssetPrice(asset), USD with 8 decimals
    body = {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
            "params": [{"to": ORACLE, "data": "0xb3596f07" + asset[2:].rjust(64, "0")}, "latest"]}
    req = urllib.request.Request(RPC, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return int(json.load(urllib.request.urlopen(req, timeout=60))["result"], 16) / 1e8


pad = lambda a: "0x" + a[2:].rjust(64, "0")
by_token = {u: s for s, (u, *_rest) in RESERVES.items()}
atokens = {pad(a): s for s, (_u, a, *_r) in RESERVES.items()}
underlyings = [u for u, *_r in RESERVES.values()]

# Optional first argument: stop at this block, to check against balanceOf at the same block.
to_block = int(sys.argv[1]) if len(sys.argv) > 1 else None
body = {
    "from_block": 0,
    "logs": [{"address": underlyings, "topics": [[TRANSFER], [], list(atokens)]},
             {"address": underlyings, "topics": [[TRANSFER], list(atokens)]}],
    "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data"]},
}
if to_block:
    body["to_block"] = to_block + 1
held = defaultdict(int)
while True:
    res = post("/query", body)
    for batch in res["data"]:
        for log in batch.get("logs") or []:
            sym = by_token.get(log["address"].lower())
            if not sym or log["topic0"] != TRANSFER:
                continue
            v = int(log["data"], 16) if log["data"] not in ("0x", None) else 0
            if atokens.get(log["topic2"]) == sym:
                held[sym] += v
            if atokens.get(log["topic1"]) == sym:
                held[sym] -= v
    last = res["next_block"]
    if last >= (to_block + 1 if to_block else res["archive_height"]):
        break
    body["from_block"] = last

rows = []
for sym, (u, _a, dec, dollar) in RESERVES.items():
    amount = held[sym] / 10 ** dec
    rows.append((amount * price(u), sym, amount, dollar))
rows.sort(reverse=True)
total = sum(r[0] for r in rows)
print(f"Held in Aave v3 on Monad up to block {last - 1:,}")
for usd, sym, amount, _d in rows:
    if usd >= 1:
        print(f"  {sym:<18} ${usd / 1e6:>7.2f}M  {usd / total:>5.1%}  ({amount:,.2f} {sym})")
dollars = sum(r[0] for r in rows if r[3])
print(f"Total ${total / 1e6:.1f}M, of which dollar tokens ${dollars / 1e6:.1f}M ({dollars / total:.1%})")
