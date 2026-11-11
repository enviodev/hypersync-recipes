"""Every fixed-rate loan on Morpho Midnight, pulled with Envio HyperSync.

Reads every market, trade, repayment, withdrawal, liquidation and collateral
deposit on Morpho Midnight on all five chains it runs on, replays each
position to find the trades that opened new debt, and prices them in dollars.
Prints how much has been borrowed, by chain, by collateral and by loan term,
then checks the replayed debt against Midnight's own position() on Ethereum.

    export ENVIO_API_TOKEN=your-token
    python script.py              # every loan up to now
    python script.py 1794355200   # only loans before this unix time (the post used 11 Nov 2026 00:00 UTC)
"""
import bisect, collections, datetime as dt, json, os, sys, time, urllib.request

TOKEN = os.environ["ENVIO_API_TOKEN"]

# Midnight core contracts, from https://docs.morpho.org/developers/contracts/addresses
MIDNIGHT = {
    "Ethereum":  ("eth",       "0x471686c42792F93528B000beF54bC10E3aa2045f", "https://ethereum-rpc.publicnode.com"),
    "Base":      ("base",      "0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A", "https://base-rpc.publicnode.com"),
    "Arc":       ("arc",       "0x208786922BE56fDE2D1Fa60e6b9eC5D723e8d7b0", "https://rpc.mainnet.arc.io"),
    "Robinhood": ("robinhood", "0x6120765Ba5336150BbdDdD0Cd9108B5bFD369632", "https://rpc.mainnet.chain.robinhood.com"),
    "Tempo":     ("tempo",     "0x31Ff800b0FA4AA42071d4ae9D0392e84f256D83D", "https://rpc.tempo.xyz"),
}

# event topic0s, from src/libraries/EventsLib.sol in https://github.com/morpho-org/midnight
MARKET_CREATED = "0xdbf3e95a2290945645820c722294f678e0b3522a7dcf3cf2e2870268bf6c9472"
TAKE = "0xbd88656d0ee14d32d4f74f814f6ccb5c750a4c542d6fdf83ee00ddca4edebff0"
UPDATE_POSITION = "0x8fd212bc8fa18d807a9b47aa2de07104bf036cfcef8ea259157085a1b618a77c"
WITHDRAW = "0x7a5e8e1731f88cf0c25f88fc7d5618e481e87be4d83f614e601850c2ff082fd7"
REPAY = "0x8b2d9c5b5a1393c4a278da77a782a77bfd7ef753c26429830b006487d3167088"
LIQUIDATE = "0xb137b989b9fd54b984273db8f16364f52f383aaca56076a320c1896e9fc2dad9"
SUPPLY_COLLATERAL = "0x968f3d07613cff19e0b1a7b034a330cfc3c90e73c1112e14495b79f436a4a074"
TOPICS = [MARKET_CREATED, TAKE, UPDATE_POSITION, WITHDRAW, REPAY, LIQUIDATE, SUPPLY_COLLATERAL]

# Chainlink ETH/USD on Ethereum, used to price WETH loans at the time they were taken
ETH_USD_AGGREGATOR = "0x7d4E742018fb52E48b08BE73d041C18B21de6Fb5"
ANSWER_UPDATED = "0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f"

USD_STABLES = {"USDC", "USDT", "PYUSD", "USDS", "USDG", "OUSD"}  # counted at $1
BTC = {"cbBTC", "WBTC", "cirBTC"}
ETH = {"WETH", "weETH", "wstETH", "cbETH", "rETH", "savETH", "cbETH-WETH-collat", "savETH-WETH-collat"}


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"User-Agent": "hypersync-recipe", "Content-Type": "application/json", **headers})
    for attempt in range(12):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception as err:
            print("retrying:", err, file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    sys.exit("request failed")


def logs(chain, addresses, topics, from_block=0):
    """Every log from these addresses with one of these topic0s, with block timestamps."""
    body = {
        "from_block": from_block,
        "logs": [{"address": addresses, "topics": [topics]}],
        "field_selection": {
            "block": ["number", "timestamp"],
            "log": ["block_number", "log_index", "address", "topic0", "topic1", "topic2", "topic3", "data"],
        },
    }
    want_addr, want_topic = {a.lower() for a in addresses}, set(topics)
    out = []
    while True:
        res = post(f"https://{chain}.hypersync.xyz/query", body, {"Authorization": "Bearer " + TOKEN})
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                if log["address"].lower() in want_addr and log["topic0"] in want_topic:
                    log["ts"] = ts[log["block_number"]]
                    out.append(log)
        if res["next_block"] >= res["archive_height"]:
            out.sort(key=lambda l: (l["block_number"], l["log_index"]))
            return out, res["archive_height"]
        body["from_block"] = res["next_block"]


def eth_call(rpc, to, data):
    res = post(rpc, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]}, {})
    return res.get("result") or "0x"


def word(data, i):
    return int(data[2 + 64 * i: 66 + 64 * i], 16)


def addr(value):
    return "0x" + (value if isinstance(value, str) else hex(value)[2:]).replace("0x", "")[-40:].rjust(40, "0")


def token_info(rpc, token, cache={}):
    """(symbol, decimals) of an ERC-20, read over RPC."""
    if (rpc, token) not in cache:
        raw = eth_call(rpc, token, "0x95d89b41")  # symbol()
        try:
            n = int(raw[66:130], 16)
            sym = bytes.fromhex(raw[130:130 + 2 * n]).decode()
        except Exception:
            sym = "?"
        dec = eth_call(rpc, token, "0x313ce567")  # decimals()
        cache[(rpc, token)] = (sym, int(dec, 16) if dec != "0x" else 18)
    return cache[(rpc, token)]


def replay(chain_logs):
    """Replay credit and debt per (market, user) and return every trade that opened new debt.

    In a Take, the buyer lends (buys credit units) and the seller borrows (sells units).
    Units first close the buyer's debt and the seller's credit; whatever is left over
    becomes new credit for the buyer and new debt for the seller. That new debt is an
    origination. The replay is checked against the totalUnitsDelta each Take emits.
    """
    pos = collections.defaultdict(lambda: [0, 0])  # (market, user) -> [credit, debt]
    loans, collateral, markets = [], collections.defaultdict(set), {}
    for l in chain_logs:
        t, d = l["topic0"], l["data"]
        if t == MARKET_CREATED:
            o = word(d, 0) // 32
            cp = o + word(d, o + 3) // 32
            markets[l["topic1"]] = {
                "loan": addr(word(d, o + 2)),
                "maturity": word(d, o + 4),
                "collaterals": [addr(word(d, cp + 1 + 4 * k)) for k in range(word(d, cp))],
            }
        elif t == TAKE:
            market, maker, taker = l["topic1"], addr(l["topic2"]), addr(l["topic3"])
            offer_is_buy, units, seller_assets = word(d, 2) == 1, word(d, 6), word(d, 8)
            delta = word(d, 12)
            delta -= 2 ** 256 if delta >= 2 ** 255 else 0
            buyer, seller = (maker, taker) if offer_is_buy else (taker, maker)
            b, s = pos[(market, buyer)], pos[(market, seller)]
            buyer_credit_up = max(units - b[1], 0)
            seller_credit_down = min(units, s[0])
            seller_debt_up = units - seller_credit_down
            assert buyer_credit_up - seller_credit_down == delta, "replay out of sync"
            b[1] -= units - buyer_credit_up
            b[0] += buyer_credit_up
            s[0] -= seller_credit_down
            s[1] += seller_debt_up
            if seller_debt_up:
                loans.append({"market": market, "borrower": seller, "lender": buyer, "ts": l["ts"],
                              # cash the borrower received for the new debt
                              "assets": seller_assets * seller_debt_up // units})
        elif t == UPDATE_POSITION:
            pos[(l["topic1"], addr(l["topic2"]))][0] -= word(d, 0)
        elif t == WITHDRAW:
            pos[(l["topic1"], addr(l["topic2"]))][0] -= word(d, 1)
        elif t == REPAY:
            pos[(l["topic2"], addr(l["topic3"]))][1] -= word(d, 0)
        elif t == LIQUIDATE:
            pos[(l["topic1"], addr(l["topic3"]))][1] -= word(d, 2) + word(d, 6)  # repaidUnits + badDebt
        elif t == SUPPLY_COLLATERAL:
            collateral[(l["topic1"], addr(l["topic3"]))].add(addr(l["topic2"]))
    return markets, loans, collateral, pos


def eth_usd_prices():
    rows, _ = logs("eth", [ETH_USD_AGGREGATOR], [ANSWER_UPDATED], 25_000_000)
    pts = sorted((int(l["data"], 16), int(l["topic1"], 16) / 1e8) for l in rows)
    times = [p[0] for p in pts]
    return lambda ts: pts[max(bisect.bisect_right(times, ts) - 1, 0)][1]


def bucket(days):
    if days <= 7:
        return "up to a week"
    if days <= 31:
        return "1 week to 1 month"
    if days <= 92:
        return "1 to 3 months"
    return "over 3 months"


def main():
    cutoff = int(sys.argv[1]) if len(sys.argv) > 1 else None
    eth_usd = eth_usd_prices()
    rows, skipped, checks = [], collections.Counter(), None
    for name, (chain, midnight, rpc) in MIDNIGHT.items():
        chain_logs, height = logs(chain, [midnight], TOPICS)
        markets, loans, collateral, pos = replay(chain_logs)
        print(f"{name}: {len(chain_logs):,} Midnight events up to block {height:,}, {len(markets):,} markets")
        for loan in loans:
            if cutoff and loan["ts"] >= cutoff:
                continue
            m = markets[loan["market"]]
            sym, dec = token_info(rpc, m["loan"])
            amount = loan["assets"] / 10 ** dec
            if sym in USD_STABLES:
                usd = amount
            elif sym == "WETH":
                usd = amount * eth_usd(loan["ts"])
            else:  # test tokens, Dummy USD Coin, and tiny non-dollar loans
                skipped[(name, sym)] += 1
                continue
            posted = {token_info(rpc, c)[0] for c in collateral.get((loan["market"], loan["borrower"]), ())}
            kind = ("Bitcoin" if posted and posted <= BTC else "ETH" if posted and posted <= ETH
                    else "Other" if posted else "Not posted by the borrower")
            rows.append({**loan, "chain": name, "usd": usd, "collateral": kind,
                         "days": (m["maturity"] - loan["ts"]) / 86400})
        if name == "Ethereum":
            checks = (midnight, rpc, pos)

    total = sum(r["usd"] for r in rows)
    last = max(r["ts"] for r in rows)
    print(f"\nBorrowed on Morpho Midnight: ${total:,.0f} across {len(rows):,} loans "
          f"(first {dt.datetime.fromtimestamp(min(r['ts'] for r in rows), dt.timezone.utc):%Y-%m-%d}, "
          f"last {dt.datetime.fromtimestamp(last, dt.timezone.utc):%Y-%m-%d %H:%M} UTC)")
    print(f"  {len({(r['chain'], r['borrower']) for r in rows}):,} borrowing wallets, "
          f"{len({(r['chain'], r['lender']) for r in rows}):,} lending wallets")

    def table(title, key):
        agg = collections.Counter()
        for r in rows:
            agg[key(r)] += r["usd"]
        print(f"\n{title}")
        for k, v in agg.most_common():
            print(f"  {k:<28} ${v:>14,.0f}  {100 * v / total:5.1f}%")

    table("By chain", lambda r: r["chain"])
    table("By collateral the borrower posted", lambda r: r["collateral"])
    table("By time from loan to maturity", lambda r: bucket(r["days"]))
    table("By month", lambda r: dt.datetime.fromtimestamp(r["ts"], dt.timezone.utc).strftime("%Y-%m"))
    print(f"\n  dollar-weighted average term: {sum(r['usd'] * r['days'] for r in rows) / total:.0f} days")
    if skipped:
        print("  left out:", ", ".join(f"{n} {s} x{c}" for (n, s), c in sorted(skipped.items())))

    # check the replay against Midnight's own storage on Ethereum
    midnight, rpc, pos = checks
    open_debt = [(k, v[1]) for k, v in pos.items() if v[1]]
    matches = 0
    for (market, user), debt in open_debt:
        # position(bytes32,address) returns credit, pendingFee, lastLossFactor, lastAccrual, debt, collateralBitmap
        raw = eth_call(rpc, midnight, "0x93c52062" + market[2:] + user[2:].rjust(64, "0"))
        matches += word(raw, 4) == debt
    print(f"\nRPC check on Ethereum: replayed debt matches position() for {matches} of {len(open_debt)} open borrows")

if __name__ == "__main__":
    main()
