# Aave v4 on Avalanche: what's deposited, by asset, with Envio HyperSync.
# Reads every Add and Remove on the Aave v4 Hub plus every Supply on its spokes, and prints
# the net amount added per asset, the biggest single day, and how many addresses have supplied.
# Stablecoins are counted at $1. Other assets are shown in their own units.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

URL = "https://avalanche.hypersync.xyz/query"
# Addresses from https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Avalanche.sol
HUB = "0xd07369fae4a5bb13c9ce446b052c7867b1abdf6e"
SPOKES = {"0x435272ceff93a1e657e8abfdf0a13e95900a3a56", "0x6a37776b5e026dbdf043b4f933c323c84dd1b514",
          "0x3b517594277c67307cf2d7cbe6fe1d4399b68c41", "0xaf22446124e566e54845f65b722e4dcbf12b650a",
          "0x2c4aea1a5f000889c6dffe8f52377afc2cb113a6"}
# Underlying tokens on Avalanche C-Chain
TOKENS = {"0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7": "WAVAX", "0x152b9d0fdc40c096757f570a51e494bd4b943e50": "BTC.b",
          "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e": "USDC", "0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7": "USDt",
          "0x49d5c2bdffac6ce2bfdb6640f4f80f226bc10bab": "WETH.e", "0xc891eb4cbdeff6e073e859e987815ed1505c2acd": "EURC",
          "0x2b2c81e08f1af8835a78bb2a90ae924ace0ea4be": "sAVAX", "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": "USDe"}
# ERC-4626 tokenization spokes, where deposits come in as vault Deposit events
VAULTS = {"0x1604d602f8a05cba2d8ff5d14de4c3498f15b6b4", "0x7cd3ccc737f442050a861ec6b00768ae96b2f58e",
          "0x01d7f7b7ce2123192fecc20bd1caf3e4d9e4c10d", "0x2e4ba06ff97e10d09fa4f5a270e97301eae729a9",
          "0xf5c849468318c8d5670020fdb96ae135fed37070", "0x7b538a1840eaf2ed92eeb67ee744ae627335e201",
          "0x6c27a7435040b7cc512319d5690beef234dfe76e"}
STABLES = {"USDC", "USDt", "USDe"}
ADD = "0xb233dd05ed21346e144167b35a6213bcf04768dbdffdc8339e8b027b94b9f305"
REMOVE = "0x535be2ff85ab4c5d0991e10dc057a4951ea2bac426ffb036eded23036a3942b2"
ADD_ASSET = "0x92fb402b777f3710166f15b30098f41042b439850df67d0195196d125458e7b3"
SUPPLY = "0xd986db228cb1fe8392c5f45ff5f2c639b7db6cbd9ca7d1fe70b2de90c2c8c961"
DEPOSIT_4626 = "0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7"

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(body):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def words(data):
    data = data[2:]
    return [int(data[i:i + 64], 16) for i in range(0, len(data), 64)]


rows, body = [], {
    "from_block": 0,
    "logs": [{"address": [HUB], "topics": [[ADD, REMOVE, ADD_ASSET]]},
             {"address": sorted(SPOKES), "topics": [[SUPPLY]]},
             {"address": sorted(VAULTS), "topics": [[DEPOSIT_4626]]}],
    "field_selection": {"block": ["number", "timestamp"],
                        "log": ["address", "block_number", "log_index", "topic0", "topic1", "topic2", "topic3", "data"]},
}
while True:
    res = post(body)
    for batch in res["data"]:
        ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
              for b in batch.get("blocks") or []}
        for log in batch.get("logs") or []:
            a, t0 = log["address"].lower(), log["topic0"]
            if (a == HUB and t0 in (ADD, REMOVE, ADD_ASSET)) or (a in SPOKES and t0 == SUPPLY) or (a in VAULTS and t0 == DEPOSIT_4626):
                rows.append((log["block_number"], log["log_index"], ts[log["block_number"]], a, t0, log))
    if res["next_block"] >= res["archive_height"]:
        break
    body["from_block"] = res["next_block"]
rows.sort()

assets, net, daily, suppliers, first = {}, defaultdict(int), defaultdict(lambda: defaultdict(int)), set(), None
for _, _, t, a, t0, log in rows:
    if t0 == ADD_ASSET:
        assets[int(log["topic1"], 16)] = (TOKENS.get("0x" + log["topic2"][-40:], log["topic2"]), words(log["data"])[0])
    elif t0 in (ADD, REMOVE):
        aid, amount = int(log["topic1"], 16), words(log["data"])[1]
        sign = 1 if t0 == ADD else -1
        net[aid] += sign * amount
        daily[datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date()][aid] += sign * amount
        if first is None and t0 == ADD:
            first = t
    elif t0 == SUPPLY:
        suppliers.add(log["topic3"][-40:])
    elif t0 == DEPOSIT_4626:
        suppliers.add(log["topic2"][-40:])

print(f"Aave v4 on Avalanche, first deposit {datetime.datetime.fromtimestamp(first, datetime.timezone.utc):%d %b %Y}")
stable_total = 0
for aid, (name, dec) in sorted(assets.items(), key=lambda kv: -net[kv[0]] / 10 ** kv[1][1]):
    amount = net[aid] / 10 ** dec
    if name in STABLES:
        stable_total += amount
        print(f"  {name:7} ${amount / 1e6:,.1f}M")
    else:
        print(f"  {name:7} {amount:,.2f} {name}")
print(f"Stablecoins ${stable_total / 1e6:,.1f}M")
print(f"Addresses that have supplied: {len(suppliers):,}")
day, by_asset = max(daily.items(), key=lambda kv: sum(v / 10 ** assets[k][1] for k, v in kv[1].items() if assets[k][0] in STABLES))
print(f"Biggest stablecoin day: {day:%d %b %Y}, "
      + ", ".join(f"+${v / 10 ** assets[k][1] / 1e6:,.1f}M {assets[k][0]}" for k, v in by_asset.items() if assets[k][0] in STABLES and v > 0))
