# Spiko SAFO on Ethereum, Arbitrum, Polygon and Base, with Envio HyperSync.
# Reads every Transfer of every SAFO share class on the four chains, rebuilds supply from mints and burns,
# counts holders, and values each class at Spiko's latest NAV and FX rates from Spiko's public API.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import json
import os
import sys
import time
import urllib.request

API = "https://public-api.spiko.io/v0"  # docs.spiko.io/developers/public_api/getting_started
SAFO_FUND = "59c2c924-ebf8-492d-a4b0-72d72ebf61e6"
CHAINS = {"Ethereum": "eth", "Arbitrum": "arbitrum", "Polygon": "polygon", "Base": "base"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0" * 40
DECIMALS = 1e5  # SAFO share classes use 5 decimals

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def get(url, body=None, headers=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", **(headers or {})})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


# 1. SAFO share classes, their token addresses, NAVs and FX rates, from Spiko's public API
classes = [s for s in get(API + "/share-classes/") if s["fundId"] == SAFO_FUND]
nav, currency = {}, {}
for s in classes:
    currency[s["symbol"]] = s["currency"]
    nav[s["symbol"]] = float(get(f"{API}/net-asset-values/{s['symbol']}/latest")["amount"]["value"])
fx = {"USD": 1.0}
for cur in {c for c in currency.values() if c != "USD"}:
    fx[cur] = float(get(f"{API}/exchange-rates/latest?fundId={SAFO_FUND}&baseCurrency={cur}&quoteCurrency=USD"
                        "&fallbackToAnyOtherFund=true")["fxRate"])

# 2. Every Transfer on each chain
total = euros = 0
holders_all = 0
print("Spiko SAFO on Ethereum, Arbitrum, Polygon and Base")
rows = []
for chain, slug in CHAINS.items():
    tokens = {t["address"].lower(): s["symbol"] for s in classes for t in s["tokens"] if t["network"] == chain}
    supply, balance = collections.Counter(), collections.Counter()
    body = {"from_block": 0, "logs": [{"address": list(tokens), "topics": [[TRANSFER]]}],
            "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data"]}}
    while True:
        res = get(f"https://{slug}.hypersync.xyz/query", body, {"Authorization": "Bearer " + TOKEN})
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                symbol = tokens.get(log["address"].lower())
                if not symbol or log["topic0"] != TRANSFER:
                    continue
                sender, receiver, value = log["topic1"][-40:], log["topic2"][-40:], int(log["data"], 16)
                if sender == ZERO:
                    supply[symbol] += value
                else:
                    balance[(symbol, sender)] -= value
                if receiver == ZERO:
                    supply[symbol] -= value
                else:
                    balance[(symbol, receiver)] += value
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]
    usd = {s: v / DECIMALS * nav[s] * fx[currency[s]] for s, v in supply.items()}
    chain_usd, chain_eur = sum(usd.values()), sum(v for s, v in usd.items() if currency[s] == "EUR")
    holders = len({a for (s, a), v in balance.items() if v > 0})
    total, euros, holders_all = total + chain_usd, euros + chain_eur, holders_all + holders
    rows.append((chain_usd, chain, chain_eur, holders))
for chain_usd, chain, chain_eur, holders in sorted(rows, reverse=True):
    print(f"  {chain:9} ${chain_usd / 1e6:7.1f}M  {100 * chain_eur / chain_usd:4.0f}% in euro classes  {holders:>4} holders")
print(f"Total ${total / 1e6:.1f}M, {100 * euros / total:.0f}% in euro share classes, {holders_all} holders across the four chains")
