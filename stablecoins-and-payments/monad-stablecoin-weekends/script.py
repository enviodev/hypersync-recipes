# Stablecoins on Monad, 30 days of transfers by UTC day, weekdays versus weekends, with Envio HyperSync.
# Counts every ERC-20 Transfer of Monad's USD stablecoins and buckets it by block timestamp.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import concurrent.futures
import datetime
import json
import os
import sys
import threading
import time
import urllib.request

HS = "https://monad.hypersync.xyz"
RPC = "https://rpc.monad.xyz"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40
# "Dollar-related" tokens from https://docs.monad.xyz/developer-essentials/network-information/tokens-and-bridges
# (staked and wrapped yield versions left out). USDC matches https://developers.circle.com/stablecoins/usdc-contract-addresses
TOKENS = {
    "0x754704bc059f8c67012fed69bc8a327a5aafb603": ("USDC", 6),
    "0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6),
    "0xe7cd86e13ac4309349f30b3435a9d337750fc82d": ("USDT0", 6),
    "0xaca92e438df0b2401ff60da7e4337b687a2435da": ("mUSD", 6),
    "0x111111d2bf19e43c34263401e0cad979ed1cdb61": ("USD1", 6),
    "0xfc421ad3c883bf9e7c4f42de845c4e4405799e73": ("GHO", 18),
    "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": ("USDe", 18),
}
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
# Optional end date (UTC, exclusive). Defaults to the start of today, so only full days are counted.
END_DAY = (datetime.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2
           else datetime.datetime.now(datetime.timezone.utc).date())
END = int(datetime.datetime.combine(END_DAY, datetime.time(), datetime.timezone.utc).timestamp())
START = END - DAYS * 86400


def post(url, body, auth=False):
    headers = {"Content-Type": "application/json", "User-Agent": "hypersync-recipe"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(2 * (attempt + 1))
    sys.exit(f"Request to {url} kept failing")


def block_time(n):
    r = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": [hex(n), False]})
    return int(r["result"]["timestamp"], 16)


def first_block_at(t):  # first block with timestamp >= t
    lo = 1
    hi = int(post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []})["result"], 16)
    while lo < hi:
        mid = (lo + hi) // 2
        if block_time(mid) < t:
            lo = mid + 1
        else:
            hi = mid
    return lo


from_block, to_block = first_block_at(START), first_block_at(END)
print(f"Reading blocks {from_block:,} to {to_block:,}", file=sys.stderr)
day = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).date()
vol = collections.defaultdict(lambda: collections.Counter())   # day -> token -> USD
cnt = collections.Counter()                                     # day -> transfers
minted, burned = collections.Counter(), collections.Counter()   # token -> USD
sent, received = collections.Counter(), collections.Counter()   # wallet -> USD
senders = set()
lock = threading.Lock()


def read_chunk(lo, hi):
    """Read every stablecoin Transfer in blocks [lo, hi) and add it to the totals."""
    body = {
        "from_block": lo, "to_block": hi,
        "logs": [{"address": list(TOKENS), "topics": [[TRANSFER]]}],
        "field_selection": {"block": ["number", "timestamp"],
                            "log": ["block_number", "address", "topic0", "topic1", "topic2", "data"]},
    }
    while True:
        res = post(HS + "/query", body, auth=True)
        rows = []
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                  for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                tok = TOKENS.get(log["address"].lower())
                if not tok or (log.get("topic0") or "").lower() != TRANSFER or not log.get("topic2"):
                    continue  # keep only logs whose address and topic0 match
                name, dec = tok
                usd = (int(log["data"][:66], 16) if log["data"] not in ("0x", None) else 0) / 10**dec
                rows.append((day(ts[log["block_number"]]), name, usd,
                             "0x" + log["topic1"][-40:], "0x" + log["topic2"][-40:]))
        with lock:
            for d, name, usd, frm, to in rows:
                vol[d][name] += usd
                cnt[d] += 1
                if frm == ZERO:
                    minted[name] += usd
                elif to == ZERO:
                    burned[name] += usd
                sent[frm] += usd
                received[to] += usd
                senders.add(frm)
        if res["next_block"] >= hi:
            return
        body["from_block"] = res["next_block"]


# Split the window into chunks and read them in parallel
step = (to_block - from_block) // 32 + 1
chunks = [(b, min(b + step, to_block)) for b in range(from_block, to_block, step)]
with concurrent.futures.ThreadPoolExecutor(16) as pool:
    for i, _ in enumerate(pool.map(lambda c: read_chunk(*c), chunks)):
        print(f"  {i + 1}/{len(chunks)} chunks read", file=sys.stderr)

short = lambda v: f"${v / 1e9:.2f}B" if v >= 1e9 else f"${v / 1e6:.1f}M"
days = sorted(vol)
total = sum(sum(vol[d].values()) for d in days)
print(f"Stablecoin transfers on Monad, {days[0]} to {days[-1]} UTC (blocks {from_block:,} to {to_block - 1:,})")
print(f"{sum(cnt.values()):,} transfers, {short(total)} moved, {len(senders):,} sending addresses\n")
names = [n for n, _ in TOKENS.values()]
print("By token:  " + "  ".join(f"{n} {short(sum(vol[d][n] for d in days))}" for n in names))
print("Net mint in window: " + "  ".join(f"{n} {minted[n] - burned[n]:+,.0f}" for n in names) + "\n")
print("Day          Weekday       Volume  Transfers")
for d in days:
    print(f"{d}  {d.strftime('%a'):>3}  {short(sum(vol[d].values())):>12}  {cnt[d]:>9,}")
wk = [d for d in days if d.weekday() >= 5]
wd = [d for d in days if d.weekday() < 5]
avg = lambda ds: sum(sum(vol[d].values()) for d in ds) / len(ds)
avgc = lambda ds: sum(cnt[d] for d in ds) / len(ds)
print(f"\nWeekend days: {len(wk)}, {short(sum(sum(vol[d].values()) for d in wk))} total, "
      f"{short(avg(wk))} a day, {avgc(wk):,.0f} transfers a day")
print(f"Weekdays:     {len(wd)}, {short(sum(sum(vol[d].values()) for d in wd))} total, "
      f"{short(avg(wd))} a day, {avgc(wd):,.0f} transfers a day")
print(f"Weekend share of volume: {sum(sum(vol[d].values()) for d in wk) / total:.1%}")
top = max(days, key=lambda d: sum(vol[d].values()))
print(f"Busiest day: {top} ({top.strftime('%A')}), {short(sum(vol[top].values()))}")
print("\nTop 5 senders by volume (wash check)")
for a, v in sent.most_common(5):
    print(f"  {a}  {short(v)}  {v / total:.1%}")
print("Top 5 receivers by volume")
for a, v in received.most_common(5):
    print(f"  {a}  {short(v)}  {v / total:.1%}")
