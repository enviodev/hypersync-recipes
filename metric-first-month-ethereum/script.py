"""Metric's first month on Ethereum: every swap, pulled with Envio HyperSync.

Metric (https://metric.xyz) went public on 15 Oct 2026. This script reads the list of Ethereum pools from
Metric's public API (the pools are created by MetricOmmPoolFactory 0x2a53833cc95548cf52c7b159110e22D3a9018f32,
see https://docs.metric.xyz/reference/supported-chains-and-deployments), then pulls every Swap event those
pools emitted and prints swaps, wallets and volume per day.

    Swap(address indexed sender, address indexed recipient, uint256 details, uint256 amountDeltas, uint256 platformFees)

amountDeltas packs two int128 values: token0's change in the top half and token1's in the bottom half.

How volume is counted: one side of each swap, in dollars. If either token is a dollar stablecoin, the
volume is the stablecoin amount. For the few pools with no stablecoin, it is the WETH amount at the Chainlink
ETH/USD answer in force at the swap's block (or, for the two gold pools, the gold amount at the Chainlink XAU/USD
answer), both read from AnswerUpdated logs with HyperSync. Metric's API price is kept as a labelled check.
"Wallets" are the addresses that sent the swap transactions.

Usage:
    export ENVIO_API_TOKEN=your-token
    python script.py
    FROM_DATE=2026-10-15 TO_DATE=2026-11-15 python script.py
"""
import bisect, collections, datetime, json, os, sys, time, urllib.request

HS = "https://eth.hypersync.xyz"
API = "https://api.metric.xyz/public/v1/evm/1/metadata"
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (https://envio.dev/app/api-tokens)")
SWAP = "0x9734819749a91fc3be03ea83205f924ee08479bd3f0da48efc91d94d050cac1e"
FROM_BLOCK = int(os.environ.get("FROM_BLOCK", 26_187_000))  # 14 Oct 2026, the day before public launch
FROM_DATE = os.environ.get("FROM_DATE", "2026-10-15")
TO_DATE = os.environ.get("TO_DATE", "2026-11-15")
ANSWER_UPDATED = "0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f"  # AnswerUpdated(int256 indexed current, uint256 indexed roundId, uint256 updatedAt)
# Chainlink aggregators on Ethereum (8 decimals) behind the ETH / USD and XAU / USD feed proxies
# 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419 and 0x214eD9Da11D2fbe465a6fc601a91E62EbEc1a0D6 (see each proxy's aggregator()).
ETH_USD = "0x7d4e742018fb52e48b08be73d041c18b21de6fb5"
XAU_USD = "0x0e3dd634ffbf7ea89bbdcf09ccc463302fd5f903"
GOLD = {"XAUt", "PAXG"}  # one troy ounce each
STABLES = {"USDC", "USDT", "DAI", "USDS", "USDe", "PYUSD", "USD1", "RLUSD", "USDG", "GHO", "FRAX", "crvUSD", "USDtb"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def post(body):
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}
    for attempt in range(30):
        try:
            req = urllib.request.Request(HS + "/query", json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception as e:  # 429s and timeouts: back off and retry
            print("retry:", e, file=sys.stderr)
            time.sleep(min(30, 3 * (attempt + 1)))
    sys.exit("HyperSync kept failing")


def pools():
    out, offset = {}, 0
    while True:
        page = get(f"{API}?count=50&offset={offset}")["data"]
        for p in page:
            out[p["poolAddress"].lower()] = p
        if len(page) < 50:
            return out
        offset += 50


def feed_answers(head):
    """Every AnswerUpdated of the two feeds from FROM_BLOCK to the head (plus a lookback so the first swaps have a price),
    as sorted block numbers and prices per feed."""
    out = {ETH_USD: [], XAU_USD: []}
    body = {"from_block": FROM_BLOCK - 300_000, "to_block": head,
            "logs": [{"address": list(out), "topics": [[ANSWER_UPDATED]]}],
            "field_selection": {"log": ["block_number", "log_index", "address", "topic0", "topic1"]}}
    while body["from_block"] < head:
        r = post(body)
        for batch in r["data"]:
            for log in batch.get("logs") or []:
                if log["address"].lower() in out and log["topic0"] == ANSWER_UPDATED:
                    out[log["address"].lower()].append((log["block_number"], log["log_index"], int(log["topic1"], 16) / 1e8))
        body["from_block"] = r["next_block"]
    return {feed: ([x[0] for x in sorted(v)], [x[2] for x in sorted(v)]) for feed, v in out.items()}


def price_at(answers, feed, block):
    blocks, prices = answers[feed]
    return prices[max(bisect.bisect_right(blocks, block) - 1, 0)]


def signed128(v):
    return v - (1 << 128) if v >> 127 else v


def main():
    P = pools()
    head = int(get(HS + "/height")["height"])
    body = {"from_block": FROM_BLOCK, "to_block": head, "logs": [{"address": list(P), "topics": [[SWAP]]}],
            "field_selection": {"log": ["block_number", "transaction_hash", "address", "data"],
                                "transaction": ["hash", "from"], "block": ["number", "timestamp"]}}
    answers = feed_answers(head)
    chainlink_usd = api_usd = 0.0  # the pools with no stablecoin, priced by Chainlink and, as a check, by Metric's API
    non_stable_swaps = 0
    day = collections.defaultdict(lambda: [0, 0.0, set()])
    by_pair, wallets, swaps = collections.Counter(), set(), 0
    while body["from_block"] < head:
        r = post(body)
        for batch in r["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) for b in batch.get("blocks") or []}
            sender = {t["hash"]: t["from"] for t in batch.get("transactions") or []}
            for log in batch.get("logs") or []:
                d = datetime.datetime.fromtimestamp(ts[log["block_number"]], datetime.UTC).strftime("%Y-%m-%d")
                if not FROM_DATE <= d <= TO_DATE:
                    continue
                p = P[log["address"]]
                packed = int(log["data"][2:][64:128], 16)
                a0 = abs(signed128(packed >> 128)) / 10 ** p["token0Decimals"]
                a1 = abs(signed128(packed & ((1 << 128) - 1))) / 10 ** p["token1Decimals"]
                if p["token1Symbol"] in STABLES:
                    usd = a1
                elif p["token0Symbol"] in STABLES:
                    usd = a0
                else:
                    api = a0 * (p.get("token0FiatPrice") or 0)  # Metric API price, check only
                    if p["token1Symbol"] == "WETH":
                        usd = a1 * price_at(answers, ETH_USD, log["block_number"])
                    elif p["token0Symbol"] == "WETH":
                        usd = a0 * price_at(answers, ETH_USD, log["block_number"])
                    elif p["token0Symbol"] in GOLD and p["token1Symbol"] in GOLD:
                        usd = a0 * price_at(answers, XAU_USD, log["block_number"])
                    else:
                        usd = api
                    chainlink_usd += usd
                    api_usd += api
                    non_stable_swaps += 1
                who = sender[log["transaction_hash"]]
                day[d][0] += 1
                day[d][1] += usd
                day[d][2].add(who)
                by_pair[p["pair"]] += usd
                wallets.add(who)
                swaps += 1
        body["from_block"] = r["next_block"]
    volume = sum(v[1] for v in day.values())
    print(f"Metric on Ethereum, {FROM_DATE} to {TO_DATE}, {len(P)} pools")
    print(f"swaps {swaps:,}  wallets {len(wallets):,}  volume ${volume:,.0f}")
    print("\nday          swaps  wallets   volume")
    for d in sorted(day):
        print(f"{d}  {day[d][0]:>6,}  {len(day[d][2]):>7,}  ${day[d][1] / 1e6:>7,.1f}M")
    print(f"\nPools with no stablecoin, {non_stable_swaps:,} swaps: ${chainlink_usd:,.0f} at Chainlink prices read with HyperSync "
          f"({100 * chainlink_usd / volume:.2f}% of volume)")
    print(f"Check (the same swaps at Metric's API price today): ${api_usd:,.0f}, gap {100 * (chainlink_usd - api_usd) / api_usd:+.1f}%")
    print("\ntop pairs by volume")
    for pair, v in by_pair.most_common(8):
        print(f"  {pair:<12} ${v / 1e6:>9,.1f}M")
    json.dump({d: {"swaps": v[0], "volume_usd": round(v[1], 2), "wallets": len(v[2])} for d, v in sorted(day.items())},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "metric_ethereum_daily.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
