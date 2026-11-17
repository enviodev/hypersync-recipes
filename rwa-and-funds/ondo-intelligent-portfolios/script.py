# Ondo Intelligent Portfolios on Ethereum and BNB Chain, with Envio HyperSync.
# Reads every mint, burn and transfer of the portfolio tokens and prints the supply per portfolio,
# its dollar value, how many addresses hold them, and how much arrived since a given date.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
#
#   python script.py               value since mid-October (12th Oct 2026)
#   python script.py 2026-10-01    value that arrived since another UTC date
import datetime
import json
import os
import sys
import time
import urllib.request
from collections import Counter, defaultdict

# Token addresses from each portfolio's page on app.ondo.finance (onchainAddresses in the page data)
TOKENS = {
    "BLKHIon":  {"eth": "0x787769d6Fc857169F5243ef66d3f0a954149d3BA", "bsc": "0xf78155dC15B838b7577002bc53bBe1041cA48622"},
    "BLKDIGon": {"eth": "0x6e17534A1Fc047907d8f422Ca166944d6469e053", "bsc": "0xe658C62195f32bc53226e7E2642e3D76B4382FB8"},
    "BLKGRWon": {"eth": "0xc90341Cb9cb8D65AF044FaB23b659b7b4279399B", "bsc": "0xE4Bd77247671746CaA3119E9FEAA146F8a4EE237"},
    "YLD8on":   {"eth": "0xA045c4477fb0a0630A50e7915a7fb4d82eDE362B", "bsc": "0x2f20d5dfbAFfa3e6351E06B8b18059747CD7ee72"},
    "YLD5on":   {"eth": "0x3D68E46bA86ebe702B2399245730DdE2f7e4B077", "bsc": "0x0Cfd1030E2431E0fA15D4cc3F3E43076FE93F8f9"},
    "MAG7Xon":  {"eth": "0xEE69f45715bfa6A4cffe2bB7e0D71093B9D58705", "bsc": "0x50436eC45316A98E72b03Ead5752E8543f11ec09"},
    "BRAINon":  {"eth": "0x8D7A1FCFaf626f8db3852c12D4cdC863D9441283", "bsc": "0x0574e53f8214d0402C8388B4402113a74354d1b0"},
}
# Token prices shown on app.ondo.finance on 4th Nov 2026. Update them for today's value.
PRICES = {"BLKHIon": 4.96, "BLKDIGon": 4.86, "BLKGRWon": 4.84, "YLD8on": 5.00, "YLD5on": 5.01, "MAG7Xon": 5.26, "BRAINon": 4.50}
CHAINS = {"eth": "https://eth.hypersync.xyz", "bsc": "https://bsc.hypersync.xyz"}
START = {"eth": 23000000, "bsc": 60000000}  # well before the tokens launched
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0" * 40

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
since = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date(2026, 10, 12)


def post(url, body):
    req = urllib.request.Request(url + "/query", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


supply, before = Counter(), Counter()
balances = defaultdict(Counter)
for chain, url in CHAINS.items():
    names = {v[chain].lower(): k for k, v in TOKENS.items()}
    body = {"from_block": START[chain], "logs": [{"address": list(names), "topics": [[TRANSFER]]}],
            "field_selection": {"block": ["number", "timestamp"], "log": ["address", "block_number", "topic0", "topic1", "topic2", "data"]}}
    while True:
        res = post(url, body)
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                  for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                name = names.get(log["address"].lower())
                if not name or log["topic0"] != TRANSFER:
                    continue
                sender, receiver = log["topic1"][-40:], log["topic2"][-40:]
                value = int(log["data"], 16) / 1e18
                day = datetime.datetime.fromtimestamp(ts[log["block_number"]], datetime.timezone.utc).date()
                change = (value if sender == ZERO else 0) - (value if receiver == ZERO else 0)
                supply[name] += change
                if day < since:
                    before[name] += change
                if sender != ZERO:
                    balances[sender][name] -= value
                if receiver != ZERO:
                    balances[receiver][name] += value
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]

usd = {k: supply[k] * PRICES[k] for k in TOKENS}
total = sum(usd.values())
earlier = sum(before[k] * PRICES[k] for k in TOKENS)
print(f"Ondo Intelligent Portfolios on Ethereum and BNB Chain: ${total / 1e6:,.1f}M")
for name, value in sorted(usd.items(), key=lambda kv: -kv[1]):
    print(f"  {name:9} ${value / 1e6:6.2f}M  {100 * value / total:4.1f}%")
holders = sum(1 for b in balances.values() if any(v > 1e-9 for v in b.values()))
print(f"Addresses holding a portfolio token: {holders:,}")
print(f"Arrived since {since:%d %b %Y}: ${(total - earlier) / 1e6:,.1f}M ({100 * (total - earlier) / total:.0f}%)")
