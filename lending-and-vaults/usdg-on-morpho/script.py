# USDG on Morpho: every market that lends Paxos USDG, and how much USDG each one holds.
# Finds the markets with Envio HyperSync (every Morpho CreateMarket event whose loan token is USDG), then
# rebuilds each market's totalSupplyAssets and totalBorrowAssets from its Supply, Withdraw, Borrow, Repay,
# AccrueInterest and Liquidate events, also with HyperSync. The chain's public RPC is only used for collateral
# token symbols and as a labelled cross-check against Morpho's market(id).
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

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
EVENTS = {
    "0xedf8870433c83823eb071d3df1caa8d008f12f6440918c20d75a3602cda30fe0": "Supply",          # data: assets, shares
    "0xa56fc0ad5702ec05ce63666221f796fb62437c32db1aa1aa075fc6484cf58fbf": "Withdraw",        # data: caller, assets, shares
    "0x570954540bed6b1304a87dfe815a5eda4a648f7097a16240dcd85c9b5fd42a43": "Borrow",          # data: caller, assets, shares
    "0x52acb05cebbd3cd39715469f22afbf5a17496295ef3bc9bb5944056c63ccaa09": "Repay",           # data: assets, shares
    "0x9d9bd501d0657d7dfe415f779a620a62b78bc508ddc0891fbbd8b7ac0f8fce87": "AccrueInterest",  # data: rate, interest, feeShares
    "0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41": "Liquidate",       # data: repaid, repaidShares, seized, badDebt, badDebtShares
}
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


def call(rpc, to, data, block="latest"):
    res = request(rpc, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, block]},
                  {"User-Agent": "Mozilla/5.0"})
    return res.get("result", "0x")


def symbol(rpc, token):
    raw = bytes.fromhex(call(rpc, token, SYMBOL)[2:])
    if len(raw) >= 96:
        size = int.from_bytes(raw[32:64], "big")
        return raw[64:64 + size].decode(errors="ignore")
    return raw.rstrip(b"\0").decode(errors="ignore") or token[:10]


def logs(url, body):
    """Page through a HyperSync log query. Returns the logs and the last block covered."""
    out = []
    while True:
        res = request(url + "/query", body, {"Authorization": "Bearer " + TOKEN})
        for batch in res["data"]:
            out += batch.get("logs") or []
        if res["next_block"] >= body.get("to_block", res["archive_height"]):
            return out, res["next_block"] - 1
        body["from_block"] = res["next_block"]


def logs_parallel(url, body, parts=48, workers=12):
    """The same query split into block ranges and pulled side by side, for busy chains with millions of logs."""
    res = request(url + "/query", {**body, "from_block": 0, "to_block": 1}, {"Authorization": "Bearer " + TOKEN})
    tip = res["archive_height"]
    edges = [tip * i // parts for i in range(parts)] + [tip]
    jobs = [{**body, "from_block": a, "to_block": b} for a, b in zip(edges, edges[1:])]
    with ThreadPoolExecutor(workers) as pool:
        out = [log for chunk, _ in pool.map(lambda j: logs(url, j), jobs) for log in chunk]
    return out, tip - 1


total, rows, checks = 0, [], []
for chain, c in CHAINS.items():
    created, _ = logs(c["hypersync"], {"from_block": 0, "logs": [{"address": [c["morpho"]], "topics": [[CREATE_MARKET]]}],
                                       "field_selection": {"log": ["address", "topic0", "topic1", "data"]}})
    markets = {}
    for log in created:
        if log["address"].lower() != c["morpho"] or log["topic0"] != CREATE_MARKET:
            continue
        words = [log["data"][2 + i:2 + i + 64] for i in range(0, 64 * 5, 64)]
        if "0x" + words[0][-40:] == c["usdg"]:
            markets[log["topic1"]] = "0x" + words[1][-40:]

    # Rebuild Morpho's totalSupplyAssets and totalBorrowAssets for every USDG market from its events.
    state = {m: [0, 0] for m in markets}   # [supply, borrow] in USDG base units (6 decimals)
    snapshot = 0
    if markets:
        events, snapshot = logs_parallel(c["hypersync"], {"from_block": 0,
                                                 "logs": [{"address": [c["morpho"]], "topics": [list(EVENTS), list(markets)]}],
                                                 "field_selection": {"log": ["address", "topic0", "topic1", "data"]}})
        for log in events:
            if log["address"].lower() != c["morpho"] or log["topic1"] not in state or log["topic0"] not in EVENTS:
                continue
            kind, st = EVENTS[log["topic0"]], state[log["topic1"]]
            w = [int(log["data"][2 + i:66 + i], 16) for i in range(0, len(log["data"]) - 2, 64)]
            if kind == "Supply":
                st[0] += w[0]
            elif kind == "Withdraw":
                st[0] -= w[1]
            elif kind == "Borrow":
                st[1] += w[1]
            elif kind == "Repay":
                st[1] -= w[0]
            elif kind == "AccrueInterest":
                st[0] += w[1]
                st[1] += w[1]
            elif kind == "Liquidate":
                st[1] -= w[0] + w[3]
                st[0] -= w[3]

    chain_total = 0
    for market_id, collateral in markets.items():
        supplied, borrowed = state[market_id][0] / 1e6, state[market_id][1] / 1e6
        if supplied >= 1:
            chain_total += supplied
            rows.append((supplied, borrowed, chain, symbol(c["rpc"], collateral) if int(collateral, 16) else "none",
                         market_id, c, snapshot))
    total += chain_total
    print(f"{chain:16} {len(markets):>4} USDG markets  ${chain_total / 1e6:,.1f}M supplied  (up to block {snapshot:,})")

borrowed_total = sum(r[1] for r in rows)
print(f"\nUSDG supplied on Morpho: ${total / 1e6:,.1f}M, of which ${borrowed_total / 1e6:,.1f}M is borrowed ({borrowed_total / total:.0%})")
top = sorted(rows, key=lambda r: r[0], reverse=True)
for supplied, borrowed, chain, collateral, *_ in top[:8]:
    print(f"  ${supplied / 1e6:>7,.1f}M supplied  ${borrowed / 1e6:>7,.1f}M borrowed  {chain:16} {collateral} collateral  ({supplied / total:.0%})")

# Cross-check, not the headline: Morpho's market(id) over public RPC at the same block, for the three biggest markets.
print("\nCheck (RPC market(id) at the same block)")
for supplied, borrowed, chain, collateral, market_id, c, snapshot in top[:3]:
    raw = call(c["rpc"], c["morpho"], MARKET + market_id[2:], hex(snapshot))[2:]
    if len(raw) < 192:
        print(f"  {chain:16} {collateral:10} RPC returned no state at block {snapshot:,}")
        continue
    rs, rb = int(raw[0:64], 16) / 1e6, int(raw[128:192], 16) / 1e6
    print(f"  {chain:16} {collateral:10} supplied ${rs:,.2f} (gap ${supplied - rs:,.2f})  borrowed ${rb:,.2f} (gap ${borrowed - rb:,.2f})")
