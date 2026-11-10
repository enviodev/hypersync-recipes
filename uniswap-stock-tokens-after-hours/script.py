# Uniswap stock token trading when the US stock market is closed, on Robinhood, with Envio HyperSync.
# Finds every Uniswap v4 pool holding a Robinhood Stock Token, reads every swap in a window, values it in USD,
# and splits volume, swaps and wallets by whether the NYSE was open (9:30 to 16:00 New York time, weekdays,
# excluding NYSE holidays). Prints the after-hours and weekend shares, the busiest after-hours tokens,
# the SPY pools since August, and writes an hour-by-weekday grid to heatmap.json.
# Python 3.9+ standard library only (3.14+ reads zstd responses, which is faster). Set ENVIO_API_TOKEN first.
#
#   python script.py                          the 30 days up to the start of today (UTC)
#   python script.py 2026-10-11 2026-11-10    any UTC window, start inclusive, end exclusive
import collections
import datetime
import json
import os
import statistics
import sys
import time
import urllib.request
import zoneinfo
from concurrent.futures import ThreadPoolExecutor

try:
    from compression import zstd
except ImportError:
    zstd = None

URL = "https://robinhood.hypersync.xyz"
# Uniswap v4 PoolManager on Robinhood (chain 4663), from https://developers.uniswap.org/docs/protocols/v4/deployments
POOL_MANAGER = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
# Robinhood Stock Tokens, from the asset API documented at https://docs.robinhood.com/chain/stock-token-apis/
ASSETS = "https://api.robinhood.com/rhj/assets"
# USDG and WETH, from https://docs.robinhood.com/chain/contracts/. Native ETH is the zero address in v4.
USDG = "0x5fc5360d0400a0fd4f2af552add042d716f1d168"
WETH = "0x0bd7d308f8e1639fab988df18a8011f41eacad73"
NATIVE = "0x" + "0" * 40
# Initialize(bytes32 indexed id, address indexed currency0, address indexed currency1, uint24 fee, int24 tickSpacing,
#            address hooks, uint160 sqrtPriceX96, int24 tick)
INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
# Swap(bytes32 indexed id, address indexed sender, int128 amount0, int128 amount1, uint160 sqrtPriceX96,
#      uint128 liquidity, int24 tick, uint24 fee)
SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
NY = zoneinfo.ZoneInfo("America/New_York")
# NYSE full-day closures, from https://www.nyse.com/trade/hours-calendars
NYSE_HOLIDAYS = {"2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
                 "2026-09-07", "2026-11-26", "2026-12-25"}
NYSE_EARLY_CLOSE = {"2026-11-27": 13, "2026-12-24": 13}  # closes at 13:00 New York time

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
SPY_ONLY = "--spy" in sys.argv  # only the pools pairing a stock token with SPY, to compare with Uniswap's numbers
dates = [a for a in sys.argv[1:] if not a.startswith("--")]
today = datetime.datetime.now(datetime.timezone.utc).date()
days = [datetime.date.fromisoformat(a) for a in dates[:2]] or [today - datetime.timedelta(days=30), today]
START, END = (int(datetime.datetime.combine(d, datetime.time(), datetime.timezone.utc).timestamp()) for d in days)


def post(path, body=None):
    headers = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
    if zstd:
        headers["Accept-Encoding"] = "zstd"
    req = urllib.request.Request(URL + path, json.dumps(body).encode() if body else None, headers)
    for attempt in range(20):
        try:
            with urllib.request.urlopen(req, timeout=300) as res:
                raw = res.read()
                if res.headers.get("Content-Encoding") == "zstd":
                    raw = zstd.decompress(raw)
                return json.loads(raw)
        except Exception:
            time.sleep(min(30, 3 * (attempt + 1)))
    sys.exit("HyperSync request kept failing")


def query(selections, start, end, log_fields, tx_fields=None):
    """Yield (log, block timestamp, tx sender) for each log matching address + topics, paging with next_block.
    Uses HyperSync's default join, which returns the transaction and block of every matching log."""
    body = {"from_block": start, "to_block": end, "logs": selections,
            "field_selection": {"log": log_fields, "block": ["number", "timestamp"]}}
    if tx_fields:
        body["field_selection"]["transaction"] = tx_fields
    while body["from_block"] < end:
        res = post("/query", body)
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                  for b in batch.get("blocks") or []}
            sender = {t["hash"]: t["from"].lower() for t in batch.get("transactions") or []}
            for log in batch.get("logs") or []:
                yield log, ts.get(log["block_number"]), sender.get(log.get("transaction_hash"))
        if res["next_block"] <= body["from_block"]:
            break
        body["from_block"] = res["next_block"]


def block_at(t, top):
    """First block with a timestamp at or after t."""
    lo, hi = 0, top
    while hi - lo > 1:
        mid = (lo + hi) // 2
        res = post("/query", {"from_block": mid, "to_block": mid + 1, "include_all_blocks": True,
                              "field_selection": {"block": ["number", "timestamp"]}})
        bt = res["data"][0]["blocks"][0]["timestamp"]
        lo, hi = (mid, hi) if (int(bt, 16) if isinstance(bt, str) else bt) < t else (lo, mid)
    return hi


def ranges(a, b, n):
    step = (b - a) // n + 1
    return [(a + i * step, min(b, a + (i + 1) * step)) for i in range(n) if a + i * step < b]


pad = lambda a: "0x" + "0" * 24 + a[2:]
addr = lambda word: ("0x" + word[-40:]).lower()


def signed(word):
    v = int(word, 16)
    return v - (1 << 256) if v >> 255 else v


def market_open(t):
    """True when the NYSE regular session is open at unix time t."""
    d = datetime.datetime.fromtimestamp(t, NY)
    day = d.strftime("%Y-%m-%d")
    if d.weekday() >= 5 or day in NYSE_HOLIDAYS:
        return False
    minutes = d.hour * 60 + d.minute
    return 570 <= minutes < NYSE_EARLY_CLOSE.get(day, 16) * 60


# 1. Robinhood Stock Tokens
req = urllib.request.Request(ASSETS, headers={"User-Agent": "Mozilla/5.0"})
STOCKS = {d["contractAddress"].lower(): (a["tokenSymbol"], int(a["tokenDecimals"]))
          for a in json.load(urllib.request.urlopen(req, timeout=60))["assets"]
          for d in a["deployments"] if d["chainId"] == 4663}
SPY = next(a for a, (s, _) in STOCKS.items() if s == "SPY")
print(f"Robinhood Stock Tokens: {len(STOCKS)}", flush=True)

# 2. Every v4 pool holding a stock token, plus ETH/USDG pools to price ETH. Filtered by token in the Initialize topics.
top = post("/height")["height"] + 1
padded = [pad(a) for a in STOCKS]
sels = [{"address": [POOL_MANAGER], "topics": [[INITIALIZE], [], padded]},
        {"address": [POOL_MANAGER], "topics": [[INITIALIZE], [], [], padded]},
        {"address": [POOL_MANAGER], "topics": [[INITIALIZE], [], [pad(NATIVE)], [pad(USDG)]]},
        {"address": [POOL_MANAGER], "topics": [[INITIALIZE], [], [pad(WETH), pad(USDG)], [pad(WETH), pad(USDG)]]}]


def find_pools(a, b):
    out = {}
    for log, _, _ in query(sels, a, b, ["block_number", "address", "topic0", "topic1", "topic2", "topic3", "data"]):
        if log["address"].lower() != POOL_MANAGER or log["topic0"] != INITIALIZE:
            continue
        out[log["topic1"].lower()] = (addr(log["topic2"]), addr(log["topic3"]))
    return out


POOLS = {}
with ThreadPoolExecutor(16) as ex:
    for part in ex.map(lambda r: find_pools(*r), ranges(0, top, 64)):
        POOLS.update(part)
DECIMALS = {USDG: 6, NATIVE: 18, WETH: 18, **{a: d for a, (_, d) in STOCKS.items()}}
ETH = {NATIVE, WETH}
# Keep pools where a stock token trades against USDG, ETH or another stock token (and the ETH/USDG pools for the
# ETH price). Pools pairing a stock token with any other token are left out: those are trades in that other token.
POOLS = {k: v for k, v in POOLS.items() if v[0] in DECIMALS and v[1] in DECIMALS and (set(v) & set(STOCKS) or USDG in v)}
STOCK_POOLS = {k for k, v in POOLS.items() if set(v) & set(STOCKS)}
SPY_POOLS = {k for k, v in POOLS.items() if SPY in v and set(v) <= set(STOCKS)}
print(f"Uniswap v4 pools trading a stock token against USDG, ETH or another stock token: {len(STOCK_POOLS):,}"
      f" ({len(SPY_POOLS)} against SPY)", flush=True)
if SPY_ONLY:  # keep the SPY pools, plus SPY/USDG pools to price SPY
    POOLS = {k: v for k, v in POOLS.items() if k in SPY_POOLS or set(v) == {SPY, USDG}}
    STOCK_POOLS = set(SPY_POOLS)

# 3. Every swap in those pools in the window: time, pool, both amounts and the wallet that sent the transaction
lo_block, hi_block = block_at(START, top), block_at(END, top)
keys = sorted(POOLS)


def read_swaps(chunk, a, b):
    rows = []
    sel = [{"address": [POOL_MANAGER], "topics": [[SWAP], chunk]}]
    for log, t, wallet in query(sel, a, b, ["block_number", "address", "topic0", "topic1", "data", "transaction_hash"],
                                ["hash", "from"]):
        pool = log["topic1"].lower()
        if log["address"].lower() != POOL_MANAGER or log["topic0"] != SWAP or pool not in POOLS:
            continue
        d = log["data"][2:]
        t0, t1 = POOLS[pool]
        rows.append((t, pool, signed(d[:64]) / 10 ** DECIMALS[t0], signed(d[64:128]) / 10 ** DECIMALS[t1], wallet,
                     log["transaction_hash"]))
    return rows


jobs = [(keys[i:i + 1000], a, b) for i in range(0, len(keys), 1000) for a, b in ranges(lo_block, hi_block, 24)]
SWAPS = []
with ThreadPoolExecutor(12) as ex:
    for rows in ex.map(lambda j: read_swaps(*j), jobs):
        SWAPS.extend(rows)
SWAPS.sort()
print(f"Swaps read: {len(SWAPS):,} (blocks {lo_block:,} to {hi_block:,})", flush=True)

# 4. USD prices per New York day: ETH from ETH/USDG swaps, then each stock token from its USDG, ETH or SPY swaps.
#    Each price is the volume-weighted median of swap prices that day, so a thin, mispriced pool barely moves it.
nyday = lambda t: datetime.datetime.fromtimestamp(t, NY).strftime("%Y-%m-%d")


def wmedian(pairs):
    pairs.sort()
    half, acc = sum(w for _, w in pairs) / 2, 0
    for p, w in pairs:
        acc += w
        if acc >= half:
            return p


PRICE = collections.defaultdict(dict)  # token -> New York day -> USD


def price(token, day):
    return 1.0 if token == USDG else PRICE[token].get(day)


# Pass 1 prices ETH and stocks against USDG, pass 2 fills stock days with no USDG trade from ETH pairs, pass 3 from SPY
for quotes in ({USDG}, ETH, {SPY}):
    samples = collections.defaultdict(list)
    for t, pool, a0, a1, _, _ in SWAPS:
        t0, t1 = POOLS[pool]
        day = nyday(t)
        for base, b_amt, quote, q_amt in ((t0, a0, t1, a1), (t1, a1, t0, a0)):
            q_usd = price(quote, day) if quote in quotes else None
            if base in STOCKS or (base in ETH and quote == USDG):
                if q_usd and b_amt and day not in PRICE[base] and abs(q_amt) * q_usd >= 10:
                    samples[(base, day)].append((abs(q_amt) * q_usd / abs(b_amt), abs(q_amt) * q_usd))
    for (base, day), pairs in samples.items():
        PRICE[base][day] = wmedian(pairs)


def usd(t, pool, a0, a1):
    """Swap size in USD: the USDG side if there is one, otherwise the side we have a price for."""
    t0, t1 = POOLS[pool]
    if USDG in (t0, t1):
        return abs(a0 if t0 == USDG else a1)
    for tok, amt in ((t0, a0), (t1, a1)):
        p = price(tok, nyday(t))
        if p:
            return abs(amt) * p
    return None


# 5. Wash check: a wallet that buys and sells the same pool on the same day, 20+ times, ending within 10% of where it
#    started, is one actor cycling volume. Those swaps are excluded from every number below.
flow = collections.defaultdict(lambda: [0, 0.0, 0.0])  # (wallet, pool, day) -> swaps, bought, sold (in token0)
for t, pool, a0, a1, wallet, _ in SWAPS:
    f = flow[(wallet, pool, nyday(t))]
    f[0] += 1
    f[1 if a0 > 0 else 2] += abs(a0)
WASH = {k for k, (n, b, s) in flow.items() if n >= 20 and min(b, s) >= 0.9 * max(b, s) and k[1] in STOCK_POOLS}

# 6. Split by market hours
tot = collections.Counter()
wallets = collections.defaultdict(set)
grid = [[0.0] * 24 for _ in range(7)]  # weekday (Mon=0) x hour, New York time
token_closed = collections.Counter()
token_all = collections.Counter()
washed = [0, 0.0]
unpriced = 0
first_day, last_day = nyday(START), nyday(END - 1)
for t, pool, a0, a1, wallet, _ in SWAPS:
    if pool not in STOCK_POOLS:
        continue
    v = usd(t, pool, a0, a1)
    if v is None:
        unpriced += 1
        continue
    if (wallet, pool, nyday(t)) in WASH:
        washed[0] += 1
        washed[1] += v
        continue
    d = datetime.datetime.fromtimestamp(t, NY)
    is_open = market_open(t)
    k = "open" if is_open else ("weekend" if d.weekday() >= 5 else "holiday" if nyday(t) in NYSE_HOLIDAYS else "night")
    tot[k + "_usd"] += v
    tot[k + "_n"] += 1
    wallets[k].add(wallet)
    grid[d.weekday()][d.hour] += v
    for tok in POOLS[pool]:  # a swap between two stock tokens counts for both
        if tok in STOCKS:
            token_all[STOCKS[tok][0]] += v
            if not is_open:
                token_closed[STOCKS[tok][0]] += v

closed = ("night", "weekend", "holiday")
all_usd = sum(tot[k + "_usd"] for k in ("open",) + closed)
all_n = sum(tot[k + "_n"] for k in ("open",) + closed)
c_usd = sum(tot[k + "_usd"] for k in closed)
c_n = sum(tot[k + "_n"] for k in closed)
c_w = set().union(*(wallets[k] for k in closed))
all_w = c_w | wallets["open"]
print(f"\nRobinhood Stock Tokens on Uniswap v4{' in pools against SPY' if SPY_ONLY else ''}, "
      f"{days[0]} to {days[1]} (UTC, end exclusive)")
print(f"Volume   ${all_usd:,.0f} from {all_n:,} swaps and {len(all_w):,} wallets")
print(f"Excluded as single-wallet cycling: {washed[0]:,} swaps, ${washed[1]:,.0f}. Unpriced swaps: {unpriced:,}")
print(f"US market closed: {c_usd / all_usd:.1%} of volume, {c_n / all_n:.1%} of swaps, "
      f"{len(c_w) / len(all_w):.1%} of wallets traded at least once while it was closed")
for k in ("open",) + closed:
    print(f"  {k:<8} ${tot[k + '_usd']:>14,.0f}  {tot[k + '_usd'] / all_usd:6.1%}   {tot[k + '_n']:>10,} swaps  "
          f"{tot[k + '_n'] / all_n:6.1%}   {len(wallets[k]):>8,} wallets")
print("Busiest stock tokens while the market is closed (volume in pools holding the token):")
for sym, v in token_closed.most_common(10):
    print(f"  {sym:<6} ${v:>13,.0f}  {v / token_all[sym]:6.1%} of its volume")
json.dump({"window": [str(days[0]), str(days[1])], "grid_usd": grid, "totals": dict(tot),
           "closed_share_usd": c_usd / all_usd, "closed_share_swaps": c_n / all_n,
           "top_closed": token_closed.most_common(10)}, open("heatmap-spy.json" if SPY_ONLY else "heatmap.json", "w"), indent=1)
