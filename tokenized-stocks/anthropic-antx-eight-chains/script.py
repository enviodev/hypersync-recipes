# xStocks ANTx (tokenized Anthropic) on eight EVM chains: every mint and burn, and how fast the first 1.5M landed.
# Uses Envio HyperSync. Python 3.9+ standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

ANTX = "0x909369940f22dc1c143ac78753a33f41597138b1"  # the same address on every chain, from xstocks.fi
CHAINS = ["Ethereum", "BNB Chain", "Arbitrum", "Optimism", "Mantle", "Ink", "HyperEVM", "Monad"]
URL = {  # HyperSync endpoint for each chain
    "Ethereum": "eth", "BNB Chain": "bsc", "Arbitrum": "arbitrum", "Optimism": "optimism",
    "Mantle": "mantle", "Ink": "ink", "HyperEVM": "hyperliquid", "Monad": "monad",
}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 64  # a zero address in a topic: the sender of a mint, the receiver of a burn
DECIMALS = 18


def num(v):
    return v if isinstance(v, int) else int(v, 16)


def post(net, body):
    req = urllib.request.Request(
        f"https://{net}.hypersync.xyz/query", json.dumps(body).encode(),
        {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:  # rate limits and timeouts: wait and try again
            time.sleep(2 * (attempt + 1))
    sys.exit("HyperSync kept failing on " + net)


def mints_and_burns(net):
    """Every mint and burn of ANTx on one chain: (timestamp, block, 'mint' or 'burn', amount)."""
    out, start = [], 0
    while True:
        r = post(net, {
            "from_block": start,
            "logs": [{"address": [ANTX], "topics": [[TRANSFER]]}],
            "field_selection": {"log": ["block_number", "topic1", "topic2", "data"],
                                "block": ["number", "timestamp"]}})
        for page in r["data"]:
            times = {num(b["number"]): num(b["timestamp"]) for b in page["blocks"]}
            for log in page["logs"]:
                kind = "mint" if log["topic1"] == ZERO else "burn" if log["topic2"] == ZERO else None
                if kind:
                    block = num(log["block_number"])
                    out.append((times[block], block, kind, num(log["data"])))
        nxt = r["next_block"]
        if nxt <= start or nxt > r["archive_height"]:
            return out
        start = nxt


def utc(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%d %b %H:%M:%S")


launch = {}  # chain -> (timestamp, amount) of its largest mint
print("ANTx, the tokenized Anthropic token from xStocks, at", ANTX)
for chain in CHAINS:
    events = mints_and_burns(URL[chain])
    supply = sum(a if k == "mint" else -a for _, _, k, a in events)
    big = max((e for e in events if e[2] == "mint"), key=lambda e: e[3])
    launch[chain] = (big[0], big[3])
    print(f"\n{chain}: supply {supply / 10 ** DECIMALS:,.0f} ANTx from {len(events)} mints and burns")
    print(f"  largest mint {big[3] / 10 ** DECIMALS:,.0f} ANTx at {utc(big[0])} UTC (block {big[1]:,})")

first = min(t for t, _ in launch.values())
last = max(t for t, _ in launch.values())
print(f"\nThe largest mint on each of {len(CHAINS)} chains landed between {utc(first)} and {utc(last)} UTC,")
print(f"{last - first} seconds apart, all at the same contract address.")
for chain, (t, a) in sorted(launch.items(), key=lambda kv: kv[1][0]):
    print(f"  +{t - first:>3}s  {chain:<10} {a / 10 ** DECIMALS:,.0f} ANTx")
