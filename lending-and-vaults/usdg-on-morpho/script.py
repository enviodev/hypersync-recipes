# USDG on Morpho: every market that lends Paxos USDG, and how much USDG each one holds.
# Finds the markets with Envio HyperSync (every Morpho CreateMarket event whose loan token is USDG),
# then reads each market's current totalSupplyAssets and totalBorrowAssets from the chain's public RPC.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import json
import os
import sys
import time
import urllib.request

# Morpho addresses: https://docs.morpho.org/get-started/resources/addresses
# USDG addresses: https://docs.paxos.com/guides/stablecoin/usdg/mainnet
CHAINS = {
    "Robinhood Chain": dict(hypersync="https://robinhood.hypersync.xyz", rpc="https://rpc.mainnet.chain.robinhood.com",
                            morpho="0x9d53d5e3bd5e8d4cbfa6db1ca238aea02e651010", usdg="0x5fc5360d0400a0fd4f2af552add042d716f1d168"),
    "Arbitrum": dict(hypersync="https://arbitrum.hypersync.xyz", rpc="https://arb1.arbitrum.io/rpc",
                     morpho="0x6c247b1f6182318877311737bac0844baa518f5e", usdg="0x004b506865409877c9fa29bfb1eba929984b9bbc"),
    "Ethereum": dict(hypersync="https://eth.hypersync.xyz", rpc="https://ethereum-rpc.publicnode.com",
                     morpho="0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb", usdg="0xe343167631d89b6ffc58b88d6b7fb0228795491d"),
}
CREATE_MARKET = "0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac"
MARKET = "0x5c60e39a"   # market(bytes32)
SYMBOL = "0x95d89b41"   # symbol()

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def request(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def call(rpc, to, data):
    res = request(rpc, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]},
                  {"User-Agent": "Mozilla/5.0"})
    return res.get("result", "0x")


def symbol(rpc, token):
    raw = bytes.fromhex(call(rpc, token, SYMBOL)[2:])
    if len(raw) >= 96:
        size = int.from_bytes(raw[32:64], "big")
        return raw[64:64 + size].decode(errors="ignore")
    return raw.rstrip(b"\0").decode(errors="ignore") or token[:10]


total, rows = 0, []
for chain, c in CHAINS.items():
    body = {"from_block": 0, "logs": [{"address": [c["morpho"]], "topics": [[CREATE_MARKET]]}],
            "field_selection": {"log": ["address", "topic0", "topic1", "data"]}}
    markets = []
    while True:
        res = request(c["hypersync"] + "/query", body, {"Authorization": "Bearer " + TOKEN})
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                if log["address"].lower() != c["morpho"] or log["topic0"] != CREATE_MARKET:
                    continue
                words = [log["data"][2 + i:2 + i + 64] for i in range(0, 64 * 5, 64)]
                if "0x" + words[0][-40:] == c["usdg"]:
                    markets.append((log["topic1"], "0x" + words[1][-40:]))
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]
    chain_total = 0
    for market_id, collateral in markets:
        state = call(c["rpc"], c["morpho"], MARKET + market_id[2:])[2:]
        supplied = int(state[0:64] or "0", 16) / 1e6    # totalSupplyAssets, USDG has 6 decimals
        borrowed = int(state[128:192] or "0", 16) / 1e6  # totalBorrowAssets
        if supplied >= 1:
            chain_total += supplied
            rows.append((supplied, borrowed, chain, symbol(c["rpc"], collateral) if int(collateral, 16) else "none"))
    total += chain_total
    print(f"{chain:16} {len(markets):>4} USDG markets  ${chain_total / 1e6:,.1f}M supplied")

borrowed_total = sum(r[1] for r in rows)
print(f"\nUSDG supplied on Morpho: ${total / 1e6:,.1f}M, of which ${borrowed_total / 1e6:,.1f}M is borrowed ({borrowed_total / total:.0%})")
for supplied, borrowed, chain, collateral in sorted(rows, reverse=True)[:8]:
    print(f"  ${supplied / 1e6:>7,.1f}M supplied  ${borrowed / 1e6:>7,.1f}M borrowed  {chain:16} {collateral} collateral  ({supplied / total:.0%})")
