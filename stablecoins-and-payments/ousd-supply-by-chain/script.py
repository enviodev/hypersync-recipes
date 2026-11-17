# Where Open USD (OUSD) sits, with Envio HyperSync.
# Replays every OUSD Transfer on Ethereum, Base and Tempo to rebuild supply and every holder's balance,
# checks the result against totalSupply() and balanceOf() onchain, and rebuilds Solana supply from every OUSD
# token balance change HyperSync returns on Solana, checked against getTokenSupply on Solana's RPC.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# Official contract addresses from https://joinopenstandard.com/integrate
EVM = {
    "Ethereum": ("eth", "https://ethereum-rpc.publicnode.com", "0x9f6F3991D525015a6F8CaF062C83b62fD3AC4436"),
    "Base": ("base", "https://mainnet.base.org", "0xB2000000000000000000002fEb517dFeC7415344"),
    "Tempo": ("tempo", "https://rpc.tempo.xyz", "0x20c0000000000000000000006a37DA5C996874BE"),
}
SOLANA_MINT = "ousd2mJsPEckLHcSCDxyKD7NDGARZcfLbDZkKiatYHB"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
SOLANA_HYPERSYNC = "https://solana.hypersync.xyz"
# OUSD's first balance change on Solana is at slot 415,382,345, inside HyperSync's Solana history (from 391,000,000).
SOLANA_FROM = 415_000_000
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

# Solana: every OUSD token account's balance change, summed. Transfers cancel out, so what's left is mints minus burns.
def solana_changes(a, b):
    body = {"from_slot": a, "to_slot": b, "account_activity": [{"mint": [SOLANA_MINT]}],
            "field_selection": {"account_activity": ["mint", "pre_token_balance", "post_token_balance"]}}
    total = 0
    while body["from_slot"] < b:
        res = post(SOLANA_HYPERSYNC + "/query", body, auth=True)
        for batch in res.get("account_activity") or []:
            for r in batch:
                if r.get("mint") == SOLANA_MINT:
                    total += int(r.get("post_token_balance") or 0) - int(r.get("pre_token_balance") or 0)
        if res["next_slot"] <= body["from_slot"]:
            time.sleep(2)
            continue
        body["from_slot"] = res["next_slot"]
    return total


# Read the RPC check first, then sum HyperSync up to the same slot so both describe the same moment.
sol = post(SOLANA_RPC, {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply",
                        "params": [SOLANA_MINT, {"commitment": "confirmed"}]})["result"]
sol_slot = sol["context"]["slot"]
sol_rpc = int(sol["value"]["amount"]) * DECIMALS // 10 ** sol["value"]["decimals"]
step = 1_000_000
with ThreadPoolExecutor(16) as pool:
    supply["Solana"] = sum(pool.map(lambda a: solana_changes(a, min(a + step, sol_slot + 1)),
                                    range(SOLANA_FROM, sol_slot + 1, step)))
diff = (sol_rpc - supply["Solana"]) / DECIMALS
checks.append(f"  Solana: rebuilt supply {'matches' if diff == 0 else f'is {diff:+,.2f} off'} getTokenSupply on Solana's "
              f"public RPC at slot {sol_slot:,}")

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
