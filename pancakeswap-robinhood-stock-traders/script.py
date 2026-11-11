"""Every PancakeSwap swap on Robinhood, and the wallets that traded a Robinhood Stock Token.

Reads every PancakeSwap v3 and Infinity CL swap on Robinhood (chain 4663) with Envio HyperSync,
counts unique wallets (transaction senders), and splits out swaps in pools that hold a stock token.
"""
import json, os, sys, time, urllib.request, urllib.error, collections, datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

URL = "https://robinhood.hypersync.xyz"
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
# PancakeSwap contracts on Robinhood, from https://developer.pancakeswap.finance/contracts/v3/addresses
# and https://developer.pancakeswap.finance/contracts/infinity/resources/addresses
V3_FACTORY = "0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865"
CL_POOL_MANAGER = "0xee04c68742e6bf434be8039580d2e89bbe55bc6f"
POOL_CREATED = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"  # v3 PoolCreated
CL_INITIALIZE = "0x426cc62fe6a33a40ba2788c2c87a9c34ee4582b95bc9fa5a7bb7ae70b750b99c"  # Infinity CL Initialize
V3_SWAP = "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83"  # PancakeSwap v3 Swap
CL_SWAP = "0x04206ad2b7c0f463bff3dd4f33c5735b0f2957a351e4f79763a4fa9e775dd237"  # Infinity CL Swap
# Robinhood Stock Tokens, from the asset API documented at https://docs.robinhood.com/chain/stock-token-apis/
ASSETS = "https://api.robinhood.com/rhj/assets"

def post(path, body=None):
    for attempt in range(8):
        try:
            req = urllib.request.Request(URL + path, json.dumps(body).encode() if body else None,
                                         {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504): raise
            time.sleep(5 * (attempt + 1))

def stream(selections, start, end, fields):
    """Yield (block_timestamps, tx_senders, logs) pages. Default join: each log comes with its block and transaction."""
    blk = start
    while blk < end:
        d = post("/query", {"from_block": blk, "to_block": end, "logs": selections, "field_selection": fields})
        ts, frm, logs = {}, {}, []
        for x in d["data"]:
            for b in x.get("blocks", []): t = b["timestamp"]; ts[b["number"]] = int(t, 16) if isinstance(t, str) else t
            for t in x.get("transactions", []): frm[t["hash"]] = t["from"].lower()
            logs += x.get("logs", [])
        yield ts, frm, logs
        if d["next_block"] <= blk: break
        blk = d["next_block"]

def main():
    height = post("/height")["height"]
    stock = {}
    req = urllib.request.Request(ASSETS, headers={"User-Agent": "Mozilla/5.0"})
    for a in json.load(urllib.request.urlopen(req, timeout=60))["assets"]:
        for dpl in a["deployments"]:
            if dpl["chainId"] == 4663: stock[dpl["contractAddress"].lower()] = a["tokenSymbol"]
    pools = {}  # v3 pool address or CL pool id -> (token0, token1)
    f = {"log": ["address", "topic0", "topic1", "topic2", "topic3", "data"]}
    for _, _, logs in stream([{"address": [V3_FACTORY], "topics": [[POOL_CREATED]]}], 0, height, f):
        for l in logs:
            if l["address"].lower() == V3_FACTORY and l["topic0"] == POOL_CREATED:
                pools["0x" + l["data"][-40:].lower()] = ("0x" + l["topic1"][-40:], "0x" + l["topic2"][-40:])
    for _, _, logs in stream([{"address": [CL_POOL_MANAGER], "topics": [[CL_INITIALIZE]]}], 0, height, f):
        for l in logs:
            if l["address"].lower() == CL_POOL_MANAGER and l["topic0"] == CL_INITIALIZE:
                pools[l["topic1"].lower()] = ("0x" + l["topic2"][-40:], "0x" + l["topic3"][-40:])
    sel = [{"topics": [[V3_SWAP]]}, {"address": [CL_POOL_MANAGER], "topics": [[CL_SWAP]]}]
    fields = {"block": ["number", "timestamp"], "log": ["address", "topic0", "topic1", "block_number", "transaction_hash"],
              "transaction": ["hash", "from"]}
    def chunk(i, n=48):
        step = height // n + 1; a, b = i * step, min(height, (i + 1) * step); rows = []
        for ts, frm, logs in stream(sel, a, b, fields):
            for l in logs:
                ad = l["address"].lower()
                # keep only logs whose address and topic0 match what we asked for
                if l["topic0"] == V3_SWAP and ad in pools: key = ad
                elif l["topic0"] == CL_SWAP and ad == CL_POOL_MANAGER: key = l["topic1"].lower()
                else: continue
                rows.append((ts[l["block_number"]], frm[l["transaction_hash"]], l["transaction_hash"], key))
        return rows
    with ThreadPoolExecutor(16) as ex:
        rows = [r for part in ex.map(chunk, range(48)) for r in part]
    txs, stock_txs, per_token = {}, set(), collections.defaultdict(set)
    for t, sender, h, key in rows:
        txs.setdefault(h, (t, sender))
        syms = [stock[a.lower()] for a in pools.get(key, ()) if a.lower() in stock]
        if syms: stock_txs.add(h)
        for s in syms: per_token[s].add(sender)
    wallets = {s for _, s in txs.values()}
    stock_wallets = {txs[h][1] for h in stock_txs}
    first = datetime.datetime.fromtimestamp(min(t for t, _ in txs.values()), datetime.timezone.utc).date()
    print(f"PancakeSwap on Robinhood, blocks up to {height:,}, first swap {first}")
    print(f"{len(rows):,} swaps in {len(txs):,} transactions from {len(wallets):,} wallets")
    print(f"{len(stock_wallets):,} wallets ({100*len(stock_wallets)/len(wallets):.1f}%) traded a Robinhood Stock Token "
          f"in {len(stock_txs):,} transactions")
    print("Most traded stock tokens by wallets:")
    for s, w in sorted(per_token.items(), key=lambda kv: -len(kv[1]))[:5]:
        print(f"  {s:6} {len(w):>7,} wallets")

    # When stock token traders trade, in New York time. US market hours are 9:30am to 4pm on weekdays;
    # NYSE holidays in the window (3 Jul, 7 Sep 2026) count as closed.
    ny, holidays = ZoneInfo("America/New_York"), {datetime.date(2026, 7, 3), datetime.date(2026, 9, 7)}
    def market_open(t):
        d = datetime.datetime.fromtimestamp(t, ny)
        return d.weekday() < 5 and d.date() not in holidays and 570 <= d.hour * 60 + d.minute < 960
    when = collections.defaultdict(set)
    for h in stock_txs:
        t, sender = txs[h]
        when[sender].add(market_open(t))
    closed_only = sum(1 for v in when.values() if v == {False})
    open_only = sum(1 for v in when.values() if v == {True})
    both = len(when) - closed_only - open_only
    print("When stock token wallets traded (New York time):")
    print(f"  only while US markets were closed {closed_only:>7,} ({100*closed_only/len(when):.1f}%)")
    print(f"  both                              {both:>7,} ({100*both/len(when):.1f}%)")
    print(f"  only during market hours          {open_only:>7,} ({100*open_only/len(when):.1f}%)")

if __name__ == "__main__":
    main()
