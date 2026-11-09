# Where BlackRock's BUIDL sits across EVM chains, with Envio HyperSync.
# Replays every BUIDL mint and burn on each EVM chain BlackRock lists, rebuilds supply per chain,
# and checks the result against totalSupply() onchain.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import json
import os
import sys
import time
import urllib.request

# Official token addresses from https://www.blackrock.com/corporate/compliance/scams-and-fraud/blackrock-token-addresses
# Ethereum has two share classes (BUIDL and BUIDL-I); both are counted for Ethereum.
EVM = {
    "Avalanche": ("avalanche", "https://avalanche-c-chain-rpc.publicnode.com", ["0x53FC82f14F009009b440a706e31c9021E1196A2F"]),
    "Ethereum": ("eth", "https://ethereum-rpc.publicnode.com", ["0x7712c34205737192402172409a8F7ccef8aA2AEc",
                                                               "0x6a9DA2D710BB9B700acde7Cb81F10F1fF8C89041"]),
    "BNB Chain": ("bsc", "https://bsc-rpc.publicnode.com", ["0x2D5BdC96D9C8AabBDB38c9A27398513e7E5ef84F"]),
    "OP Mainnet": ("optimism", "https://optimism-rpc.publicnode.com", ["0xa1CDAb15bBA75a80dF4089CaFbA013e376957cF5"]),
    "Tempo": ("tempo", "https://rpc.tempo.xyz", ["0xb5FF12Bd8010BaEf823D1BfA2Ce6bdc0109CBb24"]),
    "Arbitrum": ("arbitrum", "https://arbitrum-one-rpc.publicnode.com", ["0xA6525Ae43eDCd03dC08E775774dCAbd3bb925872"]),
    "Polygon": ("polygon", "https://polygon-bor-rpc.publicnode.com", ["0x2893Ef551B6dD69F661Ac00F11D93E5Dc5Dc0e99"]),
}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO_TOPIC = "0x" + "0" * 64
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


supply, minted_total, checks = {}, {}, []
for chain, (slug, rpc, tokens) in EVM.items():
    url = f"https://{slug}.hypersync.xyz/query"
    wanted = {t.lower() for t in tokens}
    net, minted, seen = {t: 0 for t in wanted}, 0, set()
    # Mints are Transfers from the zero address, burns are Transfers to it.
    body = {
        "from_block": 0,
        "logs": [{"address": tokens, "topics": [[TRANSFER], [ZERO_TOPIC]]},
                 {"address": tokens, "topics": [[TRANSFER], [], [ZERO_TOPIC]]}],
        "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data", "block_number", "log_index"]},
    }
    while True:
        res = post(url, body, auth=True)
        for batch in res["data"]:
            for log in batch.get("logs") or []:
                address = log["address"].lower()
                if address not in wanted or log["topic0"] != TRANSFER:
                    continue
                key = (log["block_number"], log["log_index"])
                if key in seen:
                    continue
                seen.add(key)
                value = int(log["data"], 16)
                if log["topic1"] == ZERO_TOPIC and log["topic2"] != ZERO_TOPIC:
                    net[address] += value
                    minted += value
                elif log["topic2"] == ZERO_TOPIC and log["topic1"] != ZERO_TOPIC:
                    net[address] -= value
        if res["next_block"] >= res["archive_height"]:
            break
        body["from_block"] = res["next_block"]
    block = hex(res["archive_height"] - 1)  # read onchain state at the last block HyperSync returned
    ok = all(call(rpc, t, "0x18160ddd", block) == net[t.lower()] for t in tokens)  # totalSupply()
    supply[chain], minted_total[chain] = sum(net.values()), minted
    checks.append(f"  {chain}: replayed supply {'matches' if ok else 'DOES NOT MATCH'} totalSupply() at block {int(block, 16):,}")

total = sum(supply.values())
print(f"BlackRock BUIDL on EVM chains: ${total / DECIMALS:,.0f}")
for chain, v in sorted(supply.items(), key=lambda x: -x[1]):
    print(f"  {chain:11}${v / DECIMALS:>14,.0f}  {100 * v / total:5.1f}%")
others = sum(supply[c] for c in ("Ethereum", "OP Mainnet", "Arbitrum", "Polygon"))
print(f"Avalanche vs Ethereum, OP Mainnet, Arbitrum and Polygon combined: "
      f"${supply['Avalanche'] / DECIMALS:,.0f} vs ${others / DECIMALS:,.0f}")
print(f"BUIDL minted on Avalanche since launch: ${minted_total['Avalanche'] / DECIMALS:,.0f}")
print("Checks")
print("\n".join(checks))
