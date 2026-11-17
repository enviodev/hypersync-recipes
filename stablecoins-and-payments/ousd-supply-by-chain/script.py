# Where Open USD (OUSD) sits, with Envio HyperSync.
# Replays every OUSD Transfer on Ethereum, Base and Tempo to rebuild supply and every holder's balance,
# checks the result against totalSupply() and balanceOf() onchain, and reads Solana supply from Solana's RPC.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import json
import os
import sys
import time
import urllib.request

# Official contract addresses from https://joinopenstandard.com/integrate
EVM = {
    "Ethereum": ("eth", "https://ethereum-rpc.publicnode.com", "0x9f6F3991D525015a6F8CaF062C83b62fD3AC4436"),
    "Base": ("base", "https://mainnet.base.org", "0xB2000000000000000000002fEb517dFeC7415344"),
    "Tempo": ("tempo", "https://rpc.tempo.xyz", "0x20c0000000000000000000006a37DA5C996874BE"),
}
SOLANA_MINT = "ousd2mJsPEckLHcSCDxyKD7NDGARZcfLbDZkKiatYHB"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0" * 40
DECIMALS = 10 ** 6

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(url, body, auth=False):
    headers = {"Content-Type": "application/json", "User-Agent": "curl/8"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    for attempt in range(10):
        try:
            res = json.load(urllib.request.urlopen(req, timeout=180))
            if "error" in res:
                raise ValueError(res["error"])
            return res
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def call(rpc, to, data, block):
    return int(post(rpc, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, block]})["result"], 16)


supply, top10, holders, checks = {}, {}, {}, []
for chain, (slug, rpc, token) in EVM.items():
    body = {"from_block": 0, "logs": [{"address": [token], "topics": [[TRANSFER]]}],
            "field_selection": {"log": ["topic1", "topic2", "data"]}}
    balance = collections.Counter()
    while True:
        res = post(f"https://{slug}.hypersync.xyz/query", body, auth=True)
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                value = int(log["data"][:66], 16)
                balance[log["topic1"][-40:]] -= value
                balance[log["topic2"][-40:]] += value
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]
    block = hex(res["archive_height"] - 1)  # read onchain state at the last block HyperSync returned
    minted = -balance.pop(ZERO, 0)
    onchain = call(rpc, token, "0x18160ddd", block)  # totalSupply()
    ranked = sorted(((v, a) for a, v in balance.items() if v > 0), reverse=True)
    top = ranked[:10]
    balance_ok = all(call(rpc, token, "0x70a08231" + a.rjust(64, "0"), block) == v for v, a in top)  # balanceOf()
    supply[chain], top10[chain], holders[chain] = minted, sum(v for v, a in top), len(ranked)
    checks.append(f"  {chain}: replayed supply {'matches' if minted == onchain else 'DOES NOT MATCH'} totalSupply() "
                  f"at block {int(block, 16):,}, top 10 balances {'match' if balance_ok else 'DO NOT MATCH'} balanceOf()")

sol = post(SOLANA_RPC, {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply", "params": [SOLANA_MINT]})["result"]["value"]
supply["Solana"] = int(sol["amount"]) * DECIMALS // 10 ** sol["decimals"]

total = sum(supply.values())
print(f"Open USD (OUSD) supply: ${total / DECIMALS:,.0f}")
for chain, v in sorted(supply.items(), key=lambda x: -x[1]):
    line = f"  {chain:9}${v / DECIMALS:>14,.0f}  {100 * v / total:5.1f}%"
    if chain in top10:
        line += f"  {holders[chain]:>5,} holders, top 10 hold {100 * top10[chain] / v:4.1f}%"
    print(line)
evm = sum(supply[c] for c in EVM)
print(f"Across Ethereum, Base and Tempo, the top 10 holders on each chain hold "
      f"{100 * sum(top10.values()) / evm:.1f}% of the OUSD there")
print(f"The top 10 holders on Tempo hold {100 * top10['Tempo'] / total:.1f}% of all OUSD")
print("Checks")
print("\n".join(checks))
print("  Solana supply read from getTokenSupply on Solana's public RPC")
