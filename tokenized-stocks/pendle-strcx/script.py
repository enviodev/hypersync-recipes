# Who holds STRCx on Ethereum, and how much of it sits in Pendle, with Envio HyperSync.
# STRCx is the xStocks token for Strategy's STRC preferred share, issued by Backed.
# HyperSync finds every address that has ever sent or received STRCx. Then every one of those
# addresses has its balanceOf() read over RPC at one fixed block, because STRCx pays dividends by
# raising a balance multiplier, which moves balances without any Transfer event.
# Two checks: the balances add up to totalSupply(), and Pendle's SY contract agrees with its own books.
# Python 3.9+ standard library only. Set ENVIO_API_TOKEN first.
#
#   python script.py            pull every event, save it to logs.json, print the numbers
#   python script.py --cached   reuse logs.json from an earlier run
#   python script.py 26384392   pin the balance read to a block (default: HyperSync height minus 5)
import collections
import datetime
import json
import os
import sys
import time
import urllib.request

HYPERSYNC = "https://eth.hypersync.xyz"
RPC = os.environ.get("ETH_RPC_URL", "https://eth.drpc.org")  # needs historical state for the daily series
STRCX = "0x1aad217b8f78dba5e6693460e8470f8b1a3977f3"  # Strategy PP Variable xStock (STRCx)
SY = "0x3aaaf43a1f8d327fdf24dc93654eb17e319883c5"  # Pendle SY-STRCx, yieldToken() returns STRCx
ISSUER = "0x5f7a4c11bde4f218f0025ef444c369d838ffa2ad"  # Etherscan tag "Backed: Deployer", STRCx's burner()
MULTICALL3 = "0xca11bde05977b3631167028862be2a173976ca11"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TRANSFER_SHARES = "0x9d9c909296d9c674451c0c24f02cb64981eb3b727f99865939192f880a755dcb"
ZERO = "0x" + "0" * 40

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(url, body, auth=False):
    headers = {"Content-Type": "application/json", "User-Agent": "curl/8"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:  # retry transient network errors
            if attempt == 7:
                raise
            time.sleep(2 * (attempt + 1))


def num(x):
    return int(x, 16) if isinstance(x, str) else x


def eth_call(to, data, block):
    res = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, hex(block)]})
    if "result" not in res:
        raise RuntimeError(res)
    return res["result"]


def word(n):
    return format(n, "064x")


def balances_at(addresses, block, chunk=400):
    """balanceOf(addr) on STRCx for every address, batched through Multicall3.aggregate3."""
    out = {}
    for i in range(0, len(addresses), chunk):
        part = addresses[i:i + chunk]
        n = len(part)
        head, body = "", ""
        for j, a in enumerate(part):
            head += word(n * 32 + j * 192)  # offset of tuple j inside the array
            call = "70a08231" + "0" * 24 + a[2:]  # balanceOf(address), 36 bytes
            body += "0" * 24 + STRCX[2:] + word(1) + word(0x60) + word(36) + call + "0" * 56
        data = "0x82ad56cb" + word(0x20) + word(n) + head + body
        raw = bytes.fromhex(eth_call(MULTICALL3, data, block)[2:])
        rd = lambda off: int.from_bytes(raw[off:off + 32], "big")
        base = rd(0) + 32
        for j, a in enumerate(part):
            t = base + rd(base + j * 32)
            ok, doff = rd(t), rd(t + 32)
            out[a] = rd(t + doff + 32) if ok else None
    return out


# 1. HyperSync: every Transfer and TransferShares on STRCx. Only used to find addresses and dates.
query = {
    "from_block": 0,
    "logs": [{"address": [STRCX], "topics": [[TRANSFER, TRANSFER_SHARES]]}],
    "field_selection": {
        "block": ["number", "timestamp"],
        "log": ["block_number", "log_index", "address", "topic0", "topic1", "topic2", "data"],
    },
}
CACHED = "--cached" in sys.argv and os.path.exists("logs.json")
if CACHED:
    saved = json.load(open("logs.json"))
    logs, height = saved["logs"], saved["height"]
else:
    logs = []
    while True:
        res = post(HYPERSYNC + "/query", query, auth=True)
        for batch in res["data"]:
            ts = {num(b["number"]): num(b["timestamp"]) for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                # keep only logs whose address and topic0 match exactly
                if log["address"].lower() != STRCX or log["topic0"] not in (TRANSFER, TRANSFER_SHARES):
                    continue
                logs.append({"kind": "t" if log["topic0"] == TRANSFER else "s",
                             "block": num(log["block_number"]), "ts": ts[num(log["block_number"])],
                             "from": "0x" + log["topic1"][-40:], "to": "0x" + log["topic2"][-40:],
                             "value": int(log["data"], 16)})
        if res["next_block"] >= res["archive_height"]:
            break
        query["from_block"] = res["next_block"]
    height = res["archive_height"]
    json.dump({"height": height, "logs": logs}, open("logs.json", "w"))

block = next((int(a) for a in sys.argv[1:] if a.isdigit()), height - 5)
transfers = [l for l in logs if l["kind"] == "t"]
holders = sorted({l[k] for l in logs for k in ("from", "to")} - {ZERO})
day = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")

# 2. RPC: the real balance of every address at one block, and the token's totals at the same block
bal = balances_at(holders, block)
failed = [a for a, v in bal.items() if v is None]
supply = int(eth_call(STRCX, "0x18160ddd", block), 16)
multiplier = int(eth_call(STRCX, "0x1b3ed722", block), 16) / 1e18
total = sum(v for v in bal.values() if v)

# 3. Pendle's own books: SY totalSupply() x exchangeRate() should equal the STRCx the SY holds
sy_supply = int(eth_call(SY, "0x18160ddd", block), 16)
sy_rate = int(eth_call(SY, "0x3ba0b9a9", block), 16)
sy_books = sy_supply * sy_rate // 10**18

# Transfer-summed balances, to show how far they drift from balanceOf()
naive = collections.Counter()
for l in transfers:
    naive[l["from"]] -= l["value"]
    naive[l["to"]] += l["value"]

f = lambda v: f"{v / 1e18:>12,.0f}"
pct = lambda v, d: f"{100 * v / d:5.1f}%"
nonzero = sum(1 for v in bal.values() if v)
print(f"STRCx {STRCX} on Ethereum, balances at block {block:,}")
print(f"{len(transfers):,} transfers, {len(holders):,} addresses ever touched it, {nonzero:,} hold some now")
print(f"Balance multiplier {multiplier:.4f}. Failed balance reads: {len(failed)}")
print()
print("Check 1, balances against supply")
print(f"  sum of balanceOf()  {f(total)}")
print(f"  totalSupply()       {f(supply)}   difference {(total - supply) / 1e18:,.4f}")
print("Check 2, Pendle SY against its own books")
print(f"  STRCx.balanceOf(SY)            {f(bal[SY])}")
print(f"  SY totalSupply x exchangeRate  {f(sy_books)}   difference {(bal[SY] - sy_books) / 1e18:,.2f}")
print()
others = supply - bal[SY] - bal[ISSUER]
print("Who holds STRCx")
print(f"  Pendle SY-STRCx        {f(bal[SY])}  {pct(bal[SY], supply)}")
print(f"  Backed issuer wallet   {f(bal[ISSUER])}  {pct(bal[ISSUER], supply)}")
print(f"  Everyone else          {f(others)}  {pct(others, supply)}")
print(f"  Pendle's share of STRCx outside the issuer wallet: {pct(bal[SY], supply - bal[ISSUER])}")
print()
print("Top 10 holders            balanceOf()   from Transfers    gap")
for a, v in sorted(bal.items(), key=lambda kv: -(kv[1] or 0))[:10]:
    tag = {SY: "  Pendle SY", ISSUER: "  Backed issuer"}.get(a, "")
    gap = 100 * (v - naive[a]) / v if v else 0
    print(f"  {a} {f(v)} {f(naive[a])} {gap:5.1f}%{tag}")

# 4. Pendle's SY balance at the end of each day since its first deposit, read with balanceOf() at the last
#    STRCx event block of the day. Written to sy_daily.json for the chart.
first = min(l["ts"] for l in transfers if SY in (l["from"], l["to"]))
last_block = {}
for l in logs:
    if l["ts"] >= first and l["block"] <= block:
        last_block[day(l["ts"])] = max(last_block.get(day(l["ts"]), 0), l["block"])
series = []
for d, b in sorted(last_block.items()):
    v = int(eth_call(STRCX, "0x70a08231" + "0" * 24 + SY[2:], b), 16)
    series.append({"day": d, "block": b, "sy": round(v / 1e18, 2)})
json.dump({"block": block, "supply": supply / 1e18, "sy": bal[SY] / 1e18, "issuer": bal[ISSUER] / 1e18,
           "holders": nonzero, "daily": series}, open("sy_daily.json", "w"), indent=1)
print()
print(f"Pendle SY balance since {series[0]['day']}, end of each week")
for r in series[6::7] + ([series[-1]] if (len(series) - 7) % 7 else []):
    print(f"  {r['day']}  {r['sy']:>10,.0f}")
