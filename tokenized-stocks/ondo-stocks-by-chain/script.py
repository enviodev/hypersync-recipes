# Ondo Stocks by chain: every Transfer of every Ondo stock and ETF token on Ethereum, BNB Chain, HyperEVM and
# Robinhood over one week, with Envio HyperSync. Prints transfers, value and wallets per chain, the most-moved
# tickers, and the LayerZero bridge hops between chains. Python 3.9+ standard library only. Set ENVIO_API_TOKEN first.
import calendar
import collections
import concurrent.futures
import csv
import datetime
import io
import json
import os
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

# Ondo's token sheet, linked from https://docs.ondo.finance/addresses (Ondo Stocks section)
SHEET = ("https://www.dropbox.com/scl/fi/qjfxyg748mx0dwi6up86d/EXTERNAL-Ondo-GM-Tokens-Ondo-GM-Tokens.csv"
         "?rlkey=n3no1w78wrah3umsl0nr9s77i&dl=1")
CHAINS = {  # chain id: (name, column in Ondo's sheet, LayerZero endpoint id)
    1: ("Ethereum", "Ethereum Deployed Address", 30101),
    56: ("BNB Chain", "BSC Deployed Address", 30102),
    999: ("HyperEVM", "HyperEVM Deployed Address", 30367),
    4663: ("Robinhood", "Robinhood Chain Deployed Address", 30416),
}
EID = {v[2]: v[0] for v in CHAINS.values()}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
OFT_SENT = "0x85496b760a4b7f8d66384b9df21b381f5d1b1e79f229a47aaf4c232edc2fe59a"  # OFTSent(bytes32,uint32,address,uint256,uint256)
ZERO = "0x" + "0" * 40
# Ondo's mint and redeem contracts on Ethereum and BNB Chain, from https://docs.ondo.finance/addresses
ONDO_CONTRACTS = {ZERO, "0x2c158bc456e027b2affccadf1bdbd9f5fc4c5c8c", "0xec8bbb0c90c0b5f4d8240d0f7b49da3b0aa41f4e",
                  "0xf0bc39fc911f6437c84d16188dd8294f7110f451", "0x91f8aff3738825e8eb16fc6f6b1a7a4647bdb299",
                  "0x341f9e6463161f0c90037cbc0150dc54e6d1e06e", "0x96b525b1a93f31e65f4aaf18c53842ed28525d48"}
NY = ZoneInfo("America/New_York")

# The 7 full UTC days before today. Pass a start date (YYYY-MM-DD) to pick another week.
if len(sys.argv) > 1:
    START = calendar.timegm(time.strptime(sys.argv[1], "%Y-%m-%d"))
else:
    START = calendar.timegm(datetime.datetime.now(datetime.timezone.utc).date().timetuple()) - 7 * 86400
END = START + 7 * 86400


def post(url, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "hypersync-recipe", **(headers or {})})
    for attempt in range(10):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def hypersync(chain, path, body=None):
    return json.loads(post(f"https://{chain}.hypersync.xyz{path}", body, {"Authorization": "Bearer " + TOKEN}))


def as_int(v):
    return int(v, 16) if isinstance(v, str) else v


def block_at(chain, t, top):
    """First block with a timestamp at or after t."""
    lo, hi = 0, top
    while hi - lo > 1:
        mid = (lo + hi) // 2
        r = hypersync(chain, "/query", {"from_block": mid, "to_block": mid + 1, "include_all_blocks": True,
                                        "field_selection": {"block": ["number", "timestamp"]}})
        lo, hi = (mid, hi) if as_int(r["data"][0]["blocks"][0]["timestamp"]) < t else (lo, mid)
    return hi


def read_transfers(chain, tokens, a, b):
    """Every Transfer log from the token contracts in blocks [a, b), with the transaction sender (default join)."""
    rows, blk = [], a
    while blk < b:
        r = hypersync(chain, "/query", {
            "from_block": blk, "to_block": b,
            "logs": [{"address": list(tokens), "topics": [[TRANSFER]]}],
            "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data", "block_number", "transaction_hash", "log_index"],
                                "transaction": ["hash", "from"], "block": ["number", "timestamp"]}})
        ts, sender = {}, {}
        for d in r["data"]:
            for bl in d.get("blocks") or []:
                ts[bl["number"]] = as_int(bl["timestamp"])
            for tx in d.get("transactions") or []:
                sender[tx["hash"]] = tx["from"]
        for d in r["data"]:
            for l in d.get("logs") or []:
                if (l.get("address") or "").lower() not in tokens or l.get("topic0") != TRANSFER or not l.get("topic2"):
                    continue  # keep only logs whose address and topic0 match
                rows.append(("0x" + l["topic1"][-40:], "0x" + l["topic2"][-40:], l["address"].lower(), int(l["data"] or "0x0", 16),
                             l["transaction_hash"], ts[l["block_number"]], sender.get(l["transaction_hash"])))
        if r["next_block"] <= blk:
            break
        blk = r["next_block"]
    return rows


def read_bridge_sends(chain, a, b, txs):
    """LayerZero OFTSent events in the same transactions as an Ondo token burn: one bridge hop each."""
    out, blk = [], a
    while blk < b:
        r = hypersync(chain, "/query", {"from_block": blk, "to_block": b, "logs": [{"topics": [[OFT_SENT]]}],
                                        "field_selection": {"log": ["topic0", "data", "transaction_hash"]}})
        for d in r["data"]:
            for l in d.get("logs") or []:
                if l["topic0"] == OFT_SENT and l["transaction_hash"] in txs:
                    out.append((l["transaction_hash"], int(l["data"][2:66], 16), int(l["data"][66:130], 16)))
        if r["next_block"] <= blk:
            break
        blk = r["next_block"]
    return out


def usd(n):
    return f"${n / 1e9:.2f}B" if n >= 1e9 else f"${n / 1e6:.1f}M" if n >= 1e6 else f"${n / 1e3:.1f}K" if n >= 1e3 else f"${n:.0f}"


# Ondo's stock and ETF tokens per chain, and today's price for each from CoinGecko (ids are in Ondo's sheet)
sheet = [r for r in csv.DictReader(io.StringIO(post(SHEET).decode("utf-8-sig"))) if r["Type"] in ("Stock", "ETF")]
ids = sorted({r["CoinGecko API ID"].strip() for r in sheet if r["CoinGecko API ID"].strip()})
price = {}
for i in range(0, len(ids), 100):
    got = json.loads(post("https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids=" + ",".join(ids[i:i + 100])))
    price.update({k: v.get("usd") or 0 for k, v in got.items()})
    time.sleep(3)
symbol, cg = {}, {}
for r in sheet:
    for chain, (_, col, _) in CHAINS.items():
        if r[col].strip():
            symbol[(chain, r[col].strip().lower())] = r["Symbol"]
            cg[(chain, r[col].strip().lower())] = r["CoinGecko API ID"].strip()

print(f"Ondo stocks by chain, {time.strftime('%Y-%m-%d', time.gmtime(START))} to {time.strftime('%Y-%m-%d', time.gmtime(END))} (UTC, end exclusive)\n")
results, hops = {}, []
for chain, (name, col, eid) in CHAINS.items():
    tokens = {a for (c, a) in symbol if c == chain}
    top = hypersync(chain, "/height")["height"]
    a, b = block_at(chain, START, top), block_at(chain, END, top)
    # split the range into parts and read them in parallel
    step = max(1, (b - a) // 8 + 1)
    parts = [(x, min(x + step, b)) for x in range(a, b, step)]
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        rows = [row for part in pool.map(lambda p: read_transfers(chain, tokens, *p), parts) for row in part]

    # Wash check: a wallet that moves one token through its own address 20+ times in a New York day and ends the
    # day within 10% of where it started is cycling volume. Mints, burns and Ondo's own contracts don't count.
    day = collections.defaultdict(lambda: [0, 0, 0, set()])
    for frm, to, tok, amt, tx, ts, snd in rows:
        if frm in ONDO_CONTRACTS or to in ONDO_CONTRACTS:
            continue
        k = (snd, tok, datetime.datetime.fromtimestamp(ts, NY).date())
        if to == snd:
            day[k][0] += amt; day[k][2] += 1; day[k][3].add(tx)
        if frm == snd:
            day[k][1] += amt; day[k][2] += 1; day[k][3].add(tx)
    cycling = {k: v for k, v in day.items() if v[2] >= 20 and v[0] + v[1] > 0 and abs(v[0] - v[1]) <= 0.10 * max(v[0], v[1])}
    wash_txs = set().union(*[v[3] for v in cycling.values()]) if cycling else set()
    kept = [r for r in rows if r[4] not in wash_txs]

    value = lambda r: r[3] / 1e18 * price.get(cg[(chain, r[2])], 0)  # every Ondo stock token has 18 decimals
    by_ticker = collections.Counter()
    for r in kept:
        by_ticker[symbol[(chain, r[2])]] += value(r)
    burns = {r[4]: r for r in kept if r[1] == ZERO}
    for tx, dst, amount in read_bridge_sends(chain, a, b, burns):
        tok = burns[tx][2]
        hops.append((name, EID.get(dst, str(dst)), symbol[(chain, tok)], amount / 1e18 * price.get(cg[(chain, tok)], 0)))
    results[name] = {"transfers": len(kept), "value": sum(by_ticker.values()), "wallets": len({r[6] for r in kept}),
                     "removed_as_wash": len(rows) - len(kept), "wash_wallets": len({k[0] for k in cycling}),
                     "top_tickers": by_ticker.most_common(5)}

total = sum(r["value"] for r in results.values())
count = sum(r["transfers"] for r in results.values())
print(f"Transfers {count:,}   value {usd(total)} at today's prices\n")
for name, r in results.items():
    avg = r["value"] / r["transfers"] if r["transfers"] else 0
    print(f"{name:10} {r['transfers']:>9,} transfers  {usd(r['value']):>8}  {100 * r['value'] / total if total else 0:5.1f}%  "
          f"avg {usd(avg):>7}  {r['wallets']:,} wallets")
    print("           " + ", ".join(f"{t} {usd(v)}" for t, v in r["top_tickers"]))
    if r["removed_as_wash"]:
        print(f"           left out {r['removed_as_wash']:,} transfers from {r['wash_wallets']} wallet{'s' if r['wash_wallets'] != 1 else ''} cycling volume")
print(f"\nBridge hops (LayerZero) {len(hops)}, {usd(sum(h[3] for h in hops))}")
for (src, dst), n in collections.Counter((h[0], h[1]) for h in hops).most_common():
    print(f"  {src} -> {dst}  {n}")
json.dump({"start": START, "end": END, "chains": results, "hops": hops}, open("results.json", "w"), indent=1)
