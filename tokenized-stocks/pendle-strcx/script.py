# Who holds STRCx on Ethereum, and how much of it sits in Pendle, with Envio HyperSync.
# STRCx is the xStocks token for Strategy's STRC preferred share, issued by Backed.
# STRCx pays dividends by raising a balance multiplier, which moves balances without any Transfer event.
# So HyperSync reads every TransferShares event (balances in shares, which the multiplier doesn't touch)
# and every multiplier change, and rebuilds each balance as shares x multiplier at one block.
# Checks over a public RPC at the same block: balanceOf() for every address, totalSupply(), the multiplier,
# and Pendle's SY against its own books.
# Python 3.9+ standard library only. Set ENVIO_API_TOKEN first.
#
#   python script.py            pull every event, save it to logs.json, print the numbers
#   python script.py --cached   reuse logs.json from an earlier run
#   python script.py 26384392   rebuild balances at a block (default: HyperSync height minus 5)
#   python script.py --no-check skip the RPC cross-checks
import collections
import datetime
import json
import os
import sys
import time
import urllib.request

HYPERSYNC = "https://eth.hypersync.xyz"
RPC = os.environ.get("ETH_RPC_URL", "https://eth.drpc.org")  # only for the cross-checks
STRCX = "0x1aad217b8f78dba5e6693460e8470f8b1a3977f3"  # Strategy PP Variable xStock (STRCx)
SY = "0x3aaaf43a1f8d327fdf24dc93654eb17e319883c5"  # Pendle SY-STRCx, yieldToken() returns STRCx
ISSUER = "0x5f7a4c11bde4f218f0025ef444c369d838ffa2ad"  # Etherscan tag "Backed: Deployer", STRCx's burner()
MULTICALL3 = "0xca11bde05977b3631167028862be2a173976ca11"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TRANSFER_SHARES = "0x9d9c909296d9c674451c0c24f02cb64981eb3b727f99865939192f880a755dcb"  # TransferShares(from,to,shares)
MULT_UPDATED = "0x4dbe4840d7465bd162f67814cea0b519567a2e0e578bcde61e7f4ced361e5a3d"  # MultiplierUpdated(uint256)
MULT_SCHEDULED = "0x0fc82f15d800f52869be69bb6dec5615511ff09b246f46c6fe20618c2a845d20"  # (uint256 multiplier, uint256 activatesAt)
TOPICS = (TRANSFER, TRANSFER_SHARES, MULT_UPDATED, MULT_SCHEDULED)
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


# 1. HyperSync: every Transfer, TransferShares and multiplier change on STRCx
query = {
    "from_block": 0,
    "logs": [{"address": [STRCX], "topics": [list(TOPICS)]}],
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
                if log["address"].lower() != STRCX or log["topic0"] not in TOPICS:
                    continue
                words = [int(log["data"][i:i + 64], 16) for i in range(2, len(log["data"]), 64)]
                row = {"kind": "tsum"[TOPICS.index(log["topic0"])], "block": num(log["block_number"]),
                       "idx": num(log["log_index"]), "ts": ts[num(log["block_number"])], "value": words[0]}
                if row["kind"] in "ts":
                    row["from"], row["to"] = "0x" + log["topic1"][-40:], "0x" + log["topic2"][-40:]
                if row["kind"] == "u":
                    row["at"] = row["ts"]  # takes effect now
                if row["kind"] == "m":
                    row["at"] = words[1]  # takes effect at this unix time
                logs.append(row)
        if res["next_block"] >= res["archive_height"]:
            break
        query["from_block"] = res["next_block"]
    height = res["archive_height"]
    json.dump({"height": height, "logs": logs}, open("logs.json", "w"))
logs.sort(key=lambda l: (l["block"], l["idx"]))

block = next((int(a) for a in sys.argv[1:] if a.isdigit()), height - 5)
logs = [l for l in logs if l["block"] <= block]
transfers = [l for l in logs if l["kind"] == "t"]
holders = sorted({l[k] for l in logs if l["kind"] in "ts" for k in ("from", "to")} - {ZERO})
day = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")
changes = sorted((l["at"], l["block"], l["value"]) for l in logs if l["kind"] in "um")


def multiplier_at(t):
    """The multiplier in force at unix time t: the latest change whose effective time has passed."""
    m = 10**18
    for at, _, v in changes:
        if at <= t:
            m = v
    return m


# 2. Rebuild every balance in shares from TransferShares, then convert at the multiplier in force
shares = collections.Counter()
sy_daily = {}
for l in logs:
    if l["kind"] != "s":
        continue
    shares[l["from"]] -= l["value"]
    shares[l["to"]] += l["value"]
    sy_daily[day(l["ts"])] = (l["block"], l["ts"], shares[SY])
stamp = post(HYPERSYNC + "/query", {"from_block": block, "to_block": block + 1, "include_all_blocks": True,
                                     "field_selection": {"block": ["number", "timestamp"]}}, auth=True)
end_ts = num(stamp["data"][0]["blocks"][0]["timestamp"])  # the block's own time, for the multiplier in force
mult = multiplier_at(end_ts)
bal = {a: shares[a] * mult // 10**18 for a in holders}
supply = sum(shares[a] for a in holders) * mult // 10**18
total = sum(bal.values())

# Transfer-summed balances, to show how far they drift from the real balance
naive = collections.Counter()
for l in transfers:
    naive[l["from"]] -= l["value"]
    naive[l["to"]] += l["value"]

f = lambda v: f"{v / 1e18:>12,.0f}"
pct = lambda v, d: f"{100 * v / d:5.1f}%"
nonzero = sum(1 for v in bal.values() if v)
print(f"STRCx {STRCX} on Ethereum, balances rebuilt from HyperSync at block {block:,}")
print(f"{len(transfers):,} transfers, {len(holders):,} addresses ever touched it, {nonzero:,} hold some now")
print(f"Balance multiplier {mult / 1e18:.4f}, supply {supply / 1e18:,.0f} STRCx")
print()
others = supply - bal[SY] - bal[ISSUER]
print("Who holds STRCx")
print(f"  Pendle SY-STRCx        {f(bal[SY])}  {pct(bal[SY], supply)}")
print(f"  Backed issuer wallet   {f(bal[ISSUER])}  {pct(bal[ISSUER], supply)}")
print(f"  Everyone else          {f(others)}  {pct(others, supply)}")
print(f"  Pendle's share of STRCx outside the issuer wallet: {pct(bal[SY], supply - bal[ISSUER])}")
print()
print("Top 10 holders          rebuilt balance   from Transfers    gap")
for a, v in sorted(bal.items(), key=lambda kv: -kv[1])[:10]:
    tag = {SY: "  Pendle SY", ISSUER: "  Backed issuer"}.get(a, "")
    gap = 100 * (v - naive[a]) / v if v else 0
    print(f"  {a} {f(v)} {f(naive[a])} {gap:5.1f}%{tag}")

# 3. Pendle's SY balance at the end of each day since its first deposit: its shares after the day's last
#    STRCx event, at the multiplier in force then. Written to sy_daily.json for the chart.
first = min(l["ts"] for l in transfers if SY in (l["from"], l["to"]))
series = [{"day": d, "block": b, "sy": round(sh * multiplier_at(t) // 10**18 / 1e18, 2)}
          for d, (b, t, sh) in sorted(sy_daily.items()) if t >= first]
json.dump({"block": block, "supply": supply / 1e18, "sy": bal[SY] / 1e18, "issuer": bal[ISSUER] / 1e18,
           "holders": nonzero, "daily": series}, open("sy_daily.json", "w"), indent=1)
print()
print(f"Pendle SY balance since {series[0]['day']}, end of each week")
for r in series[6::7] + ([series[-1]] if (len(series) - 7) % 7 else []):
    print(f"  {r['day']}  {r['sy']:>10,.0f}")

# 4. Cross-checks over a public RPC at the same block. Not used for any number above.
if "--no-check" not in sys.argv:
    rpc_bal = balances_at(holders, block)
    off = [a for a in holders if rpc_bal[a] is None or abs(rpc_bal[a] - bal[a]) > 1]
    rpc_supply = int(eth_call(STRCX, "0x18160ddd", block), 16)
    rpc_mult = int(eth_call(STRCX, "0x1b3ed722", block), 16)
    sy_books = int(eth_call(SY, "0x18160ddd", block), 16) * int(eth_call(SY, "0x3ba0b9a9", block), 16) // 10**18
    print()
    print(f"Check (RPC, block {block:,})")
    print(f"  balanceOf() for all {len(holders):,} addresses: {len(holders) - len(off):,} match the rebuilt balance, "
          f"{len(off)} differ by more than 1 wei")
    print(f"  multiplier()   {rpc_mult / 1e18:.6f}   rebuilt {mult / 1e18:.6f}")
    print(f"  totalSupply()  {f(rpc_supply)}   rebuilt {f(supply)}   difference {(supply - rpc_supply) / 1e18:,.4f}")
    print(f"  Pendle SY totalSupply x exchangeRate  {f(sy_books)}   rebuilt SY balance {f(bal[SY])}")
