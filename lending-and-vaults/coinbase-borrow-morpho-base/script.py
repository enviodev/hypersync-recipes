# Coinbase borrowing on Morpho, Base: the cbBTC/USDC market behind Coinbase's bitcoin-backed loans,
# plus the new PAXG/USDC market behind its gold-backed loans.
# Reads every SupplyCollateral, WithdrawCollateral, Borrow, Repay and Liquidate event in both markets with
# Envio HyperSync and rebuilds collateral, borrowers and USDC owed from them. The dollar price of each collateral
# token comes from HyperSync too, from the AnswerUpdated logs of the Chainlink aggregator the market's oracle reads.
# Base's public RPC is used for the oracle price and as labelled cross-checks of the price and of USDC owed.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
#   python script.py              # full history up to now
#   python script.py 55220000     # stop at a fixed Base block to rerun a past snapshot exactly
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import datetime, timezone

HYPERSYNC = "https://base.hypersync.xyz"
RPC = "https://mainnet.base.org"
MORPHO = "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb"  # https://docs.morpho.org/get-started/resources/addresses
MARKETS = {  # market ids from the Morpho API (https://api.morpho.org/graphql), loan token USDC on both
    "cbBTC": dict(id="0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836", decimals=8,
                  token="0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"),   # Coinbase Wrapped BTC
    "PAXG": dict(id="0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392", decimals=18,
                 token="0xe904aea5e1b110c9174728fa2effc8aed19e98ef"),    # https://docs.paxos.com/guides/stablecoin/paxg/mainnet
}
T = {
    "0xa3b9472a1399e17e123f3c2e6586c23e504184d504de59cdaa2b375e880c6184": "SupplyCollateral",
    "0xe80ebd7cc9223d7382aab2e0d1d6155c65651f83d53c8b9b06901d167e321142": "WithdrawCollateral",
    "0x570954540bed6b1304a87dfe815a5eda4a648f7097a16240dcd85c9b5fd42a43": "Borrow",
    "0x52acb05cebbd3cd39715469f22afbf5a17496295ef3bc9bb5944056c63ccaa09": "Repay",
    "0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41": "Liquidate",
}


ANSWER_UPDATED = "0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f"  # AnswerUpdated(int256 indexed current, uint256 indexed roundId, uint256 updatedAt)
# Chainlink aggregators (8 decimals) behind each market's oracle. Both oracles scale the feed answer straight to USDC
# per token, so the price is the answer divided by 1e8. Found from the oracle's BASE_FEED_1() (for PAXG, the primary
# oracle's BASE_FEED_1() behind the wrapper that can fall back to a PAXG / USD feed), then the proxy's aggregator().
FEEDS = {
    "cbBTC": "0xe5ec87a39445b8d5b751b116802a53c5ae7e9df1",  # Chainlink BTC / USD
    "PAXG": "0x3591ffd547db65020c18e80fce399cf167b2bdce",   # Chainlink XAU / USD, gold per troy ounce, and one PAXG is one ounce
}

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
TO_BLOCK = int(sys.argv[1]) if len(sys.argv) > 1 else None
POOL = ThreadPoolExecutor(12)


def request(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def call(to, data, block):
    res = request(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                        "params": [{"to": to, "data": data}, hex(block)]}, {"User-Agent": "Mozilla/5.0"})
    return res.get("result", "0x")[2:]


def page(body):
    """Page through one HyperSync query over [from_block, to_block). Returns its logs and block times."""
    out, ts = [], {}
    while True:
        res = request(HYPERSYNC + "/query", body, {"Authorization": "Bearer " + TOKEN})
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                ts[b["number"]] = int(b["timestamp"], 16)
            out += batch.get("logs") or []
        if res["next_block"] >= body["to_block"]:
            return out, ts
        body["from_block"] = res["next_block"]


def pull(selection, fields, parts=48):
    """One query split into block ranges and pulled side by side (the cbBTC market has millions of logs).
    Logs come back in block order."""
    end = TO_BLOCK + 1 if TO_BLOCK else request(HYPERSYNC + "/query", {"from_block": 0, "to_block": 1, "logs": [selection]},
                                                {"Authorization": "Bearer " + TOKEN})["archive_height"]
    edges = [end * i // parts for i in range(parts)] + [end]
    jobs = [{"from_block": a, "to_block": b, "logs": [selection], "field_selection": fields} for a, b in zip(edges, edges[1:])]
    out, ts = [], {}
    for logs, times in POOL.map(page, jobs):
        out += logs
        ts.update(times)
    return out, ts, end - 1


def latest_answer(feed, end):
    """Latest AnswerUpdated of a Chainlink feed before block `end`, read with HyperSync: (USD price, updatedAt).
    Looks back over a growing window of blocks until the feed has an answer."""
    window = 200_000
    while True:
        body = {"from_block": max(end - window, 0), "to_block": end, "logs": [{"address": [feed], "topics": [[ANSWER_UPDATED]]}],
                "field_selection": {"log": ["block_number", "log_index", "address", "topic0", "topic1", "data"]}}
        best = None
        while True:
            res = request(HYPERSYNC + "/query", body, {"Authorization": "Bearer " + TOKEN})
            for batch in res["data"]:
                for log in batch.get("logs") or []:
                    if log["address"].lower() == feed and log["topic0"] == ANSWER_UPDATED:
                        key = (log["block_number"], log["log_index"])
                        if best is None or key > best[0]:
                            best = (key, int(log["topic1"], 16) / 1e8, int(log["data"], 16))
            if res["next_block"] >= end:
                break
            body["from_block"] = res["next_block"]
        if best or end - window <= 0:
            return (best[1], best[2]) if best else None
        window *= 4


def events(market_id):
    """Every collateral, borrow, repay and liquidation log in one market, with its block time."""
    logs, ts, last = pull({"address": [MORPHO], "topics": [list(T), [market_id]]},
                          {"log": ["block_number", "address", "topic0", "topic1", "topic2", "topic3", "data"],
                           "block": ["number", "timestamp"]})
    out = [log for log in logs if log["address"].lower() == MORPHO and log["topic0"] in T and log["topic1"] == market_id]
    for log in out:
        log["time"] = ts[log["block_number"]]
    return out, last


def words(data):
    return [int(data[2 + i:66 + i], 16) for i in range(0, len(data) - 2, 64)]


def month(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")


snapshot = TO_BLOCK
for name, m in MARKETS.items():
    logs, last = events(m["id"])
    snapshot = snapshot or last
    scale = 10 ** m["decimals"]
    collateral, borrowed, repaid = 0.0, 0.0, 0.0
    debt_shares, rate = 0, (0, 1)   # Morpho tracks debt in shares; rate is assets per share from the latest event
    borrowers, monthly = set(), {}
    for log in logs:
        kind, w = T[log["topic0"]], words(log["data"])
        if kind == "SupplyCollateral":
            collateral += w[0] / scale
        elif kind == "WithdrawCollateral":
            collateral -= w[1] / scale
        elif kind == "Borrow":
            debt_shares += w[2]
            rate = (w[1], w[2])
            borrowed += w[1] / 1e6
            borrowers.add("0x" + log["topic2"][-40:])
        elif kind == "Repay":
            debt_shares -= w[1]
            rate = (w[0], w[1])
            repaid += w[0] / 1e6
        elif kind == "Liquidate":
            debt_shares -= w[1] + w[4]   # repaid shares and bad debt shares
            collateral -= w[2] / scale
            repaid += (w[0] + w[3]) / 1e6
        monthly[month(log["time"])] = (collateral, borrowed - repaid)

    owed = debt_shares * rate[0] / rate[1] / 1e6   # debt shares outstanding at the latest event's rate, so with interest

    # Chainlink price from HyperSync for dollar values. Over RPC, the oracle price() and Morpho market() are cross-checks.
    s = call(MORPHO, "0x5c60e39a" + m["id"][2:], snapshot)
    rpc_owed = int(s[128:192], 16) / 1e6                               # totalBorrowAssets
    params = call(MORPHO, "0x2c3c9157" + m["id"][2:], snapshot)        # idToMarketParams(bytes32)
    oracle = "0x" + params[64 * 2 + 24:64 * 3]
    price, price_time = latest_answer(FEEDS[name], snapshot + 1)                            # USDC per token
    oracle_price = int(call(oracle, "0xa035b1fe", snapshot), 16) / 10 ** (36 + 6 - m["decimals"])  # oracle price(), check only
    first = datetime.fromtimestamp(logs[0]["time"], timezone.utc).strftime("%Y-%m-%d") if logs else "none"

    print(f"{name}/USDC market {m['id']} (oracle {oracle}), up to Base block {snapshot:,}")
    print(f"  collateral now: {collateral:,.4f} {name} ~ ${collateral * price:,.0f} at ${price:,.2f} per {name} (Chainlink feed, HyperSync)")
    print(f"  Check (oracle price() over RPC): ${oracle_price:,.2f} per {name}, gap {100 * (price - oracle_price) / oracle_price:+.2f}%")
    print(f"  USDC owed now: ${owed:,.0f} (HyperSync, debt shares outstanding times the latest borrow or repay rate)")
    print(f"  Check (RPC totalBorrowAssets): ${rpc_owed:,.0f}, gap ${owed - rpc_owed:,.2f}")
    print(f"  ${borrowed:,.0f} borrowed in total since {first}")
    print(f"  {len(borrowers):,} unique borrowers, {len(logs):,} collateral, borrow, repay and liquidation events")
    print("  end of each month: collateral, USDC principal outstanding (borrows minus repays)")
    for mo, (c, d) in sorted(monthly.items()):
        print(f"    {mo}  {c:>14,.4f} {name}  ${d:>16,.0f}")
    print()
