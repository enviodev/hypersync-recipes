"""Who holds Backpack's tokenized stocks on Solana, counted with Envio HyperSync.

HyperSync's account_activity table has one row for every token account a transaction touched, with the
balance after the transaction. Filter it by mint, keep the latest row for each token account, and you
have every holder's balance without asking an RPC node for program accounts.

This reads the full history of the 94 mints in mints.json (about 580M rows from June 2026 to today), so
it works through the slot range in 100K-slot pieces, saves each piece under chunks/ and picks up where
it left off if you stop it. Balances are priced with Jupiter's price API and summed per wallet.

Usage:
    export ENVIO_API_TOKEN=your-token
    python holders.py
    WORKERS=16 python holders.py
"""
import collections, glob, json, os, pickle, sys, time, urllib.request
from multiprocessing import Pool

HS = "https://solana.hypersync.xyz"
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (https://envio.dev/app/api-tokens)")
HERE = os.path.dirname(os.path.abspath(__file__))
MINTS = json.load(open(os.path.join(HERE, "mints.json")))  # ticker -> mint
TICKER = {mint: ticker for ticker, mint in MINTS.items()}
DECIMALS = 6
START = 420_000_000  # before the first of these mints was created
CHUNK = 100_000
WORKERS = int(os.environ.get("WORKERS", 16))
CACHE = os.path.join(HERE, "chunks")


def post(body):
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}
    for attempt in range(60):
        try:
            req = urllib.request.Request(HS + "/query", json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:  # 429s and timeouts: back off and retry
            time.sleep(min(30, 2 * (attempt + 1)))
    sys.exit("HyperSync kept failing")


def pull(ab):
    """Latest balance row for every token account touched in [a, b)."""
    a, b = ab
    path = os.path.join(CACHE, f"{a}.pkl")
    if os.path.exists(path):
        return 0
    last, rows, cur = {}, 0, a
    while cur < b:
        r = post({"from_slot": cur, "to_slot": b, "account_activity": [{"mint": list(MINTS.values())}],
                  "field_selection": {"account_activity": ["slot", "transaction_index", "account", "mint",
                                                           "post_owner", "post_token_balance"]}})
        for batch in r.get("account_activity") or []:
            for x in batch:
                rows += 1
                key = (x["slot"], x["transaction_index"])
                prev = last.get(x["account"])
                if prev is None or key >= prev[0]:
                    last[x["account"]] = (key, x["mint"], x.get("post_owner"), x.get("post_token_balance"))
        if r["next_slot"] <= cur:
            time.sleep(1)
            continue
        cur = r["next_slot"]
    pickle.dump((rows, last), open(path + ".tmp", "wb"))
    os.rename(path + ".tmp", path)
    return rows


def prices(mints):
    out = {}
    for i in range(0, len(mints), 50):
        url = "https://lite-api.jup.ag/price/v3?ids=" + ",".join(mints[i:i + 50])
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        for mint, v in json.load(urllib.request.urlopen(req, timeout=30)).items():
            out[mint] = v["usdPrice"]
    return out


def main():
    os.makedirs(CACHE, exist_ok=True)
    end_file = os.path.join(CACHE, "end_slot.txt")
    if os.path.exists(end_file):  # keep one snapshot slot across restarts
        end = int(open(end_file).read())
    else:
        end = int(urllib.request.urlopen(HS + "/height").read())
        open(end_file, "w").write(str(end))
    ranges = [(a, min(a + CHUNK, end)) for a in range(START, end, CHUNK)]
    with Pool(WORKERS) as pool:
        for i, _ in enumerate(pool.imap_unordered(pull, ranges)):
            if i % 25 == 0:
                print(f"{i}/{len(ranges)} slot ranges", file=sys.stderr, flush=True)

    last, rows = {}, 0
    for path in glob.glob(os.path.join(CACHE, "*.pkl")):
        n, part = pickle.load(open(path, "rb"))
        rows += n
        for account, v in part.items():
            if account not in last or v[0] >= last[account][0]:
                last[account] = v

    px = prices(list(MINTS.values()))
    wallet = collections.defaultdict(float)
    per = collections.defaultdict(lambda: collections.defaultdict(float))
    for _, mint, owner, balance in last.values():
        if owner is None or not balance or int(balance) == 0:  # closed or empty token account
            continue
        usd = int(balance) / 10**DECIMALS * px.get(mint, 0)
        wallet[owner] += usd
        per[mint][owner] += usd

    print(f"snapshot slot {end:,}, {rows:,} balance rows read")
    print(f"value held            ${sum(wallet.values()):,.0f}")
    print(f"wallets holding any   {len(wallet):,}")
    for floor in (1, 10, 100, 1000):
        print(f"wallets holding ${floor}+ {sum(1 for v in wallet.values() if v >= floor):>10,}")
    print("\nticker      value   wallets $1+")
    table = sorted(((sum(v.values()), sum(1 for u in v.values() if u >= 1), TICKER[m]) for m, v in per.items()), reverse=True)
    for value, holders, ticker in table:
        print(f"{ticker:<6} ${value:>12,.0f} {holders:>10,}")


if __name__ == "__main__":
    main()
