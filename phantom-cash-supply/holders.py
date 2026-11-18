"""Count wallets holding Phantom CASH, with Envio HyperSync.

HyperSync's account_activity table has one row for every token account a transaction touched, with the
balance after the transaction. Filter it by the CASH mint, keep the latest row for each token account, and
you have every holder's balance without asking an RPC node for program accounts.

HyperSync's Solana history starts at slot 391,000,000 (3 Jan 2026). A CASH account that hasn't moved since
then has no row, so the script reads Solana RPC getTokenSupply at the end only as a labelled check and prints
how much CASH sits in accounts HyperSync hasn't seen. It writes the supply and its slot to snapshot.json, which
script.py starts from.

The full range is about 80M slots, so the script works through it in 200K-slot pieces, saves each piece
under chunks/ and picks up where it left off if you stop it.

Usage:
    export ENVIO_API_TOKEN=your-token
    python holders.py
    WORKERS=16 python holders.py
"""
import collections, glob, json, os, pickle, sys, time, urllib.request
from multiprocessing import Pool

HS = "https://solana.hypersync.xyz"
RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (https://envio.dev/app/api-tokens)")
CASH = "CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH"
DECIMALS = 6
START = 391_000_000  # the start of HyperSync's Solana history
CHUNK = 200_000
WORKERS = int(os.environ.get("WORKERS", 16))
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "chunks")


def post(url, body, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    for attempt in range(60):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:  # 429s and timeouts: back off and retry
            time.sleep(min(30, 2 * (attempt + 1)))
    sys.exit("Request kept failing: " + url)


def pull(ab):
    """Latest balance row for every CASH token account touched in [a, b)."""
    a, b = ab
    path = os.path.join(CACHE, f"{a}-{b}.pkl")
    if os.path.exists(path):
        return 0
    last, rows, stalls = {}, 0, 0
    body = {"from_slot": a, "to_slot": b, "account_activity": [{"mint": [CASH]}],
            "field_selection": {"account_activity": ["slot", "transaction_index", "account", "mint",
                                                     "post_owner", "post_token_balance"]}}
    while body["from_slot"] < b:
        r = post(HS + "/query", body)
        for batch in r.get("account_activity") or []:
            for x in batch:
                if x.get("mint") != CASH:
                    continue
                rows += 1
                key = (x["slot"], x["transaction_index"])
                prev = last.get(x["account"])
                if prev is None or key >= prev[0]:
                    last[x["account"]] = (key, x.get("post_owner"), int(x.get("post_token_balance") or 0))
        if r["next_slot"] <= body["from_slot"]:
            stalls += 1
            if stalls > 20:
                raise RuntimeError(f"no progress at slot {body['from_slot']}")
            time.sleep(2)
            continue
        stalls = 0
        body["from_slot"] = r["next_slot"]
    pickle.dump((rows, last), open(path + ".tmp", "wb"))
    os.rename(path + ".tmp", path)
    return rows


def main():
    os.makedirs(CACHE, exist_ok=True)
    end_file = os.path.join(CACHE, "end_slot.txt")
    if os.path.exists(end_file):  # keep one snapshot slot across restarts
        end = int(open(end_file).read())
    else:
        end = int(urllib.request.urlopen(HS + "/height").read())
        open(end_file, "w").write(str(end))
    done = [tuple(map(int, os.path.basename(p)[:-4].split("-"))) for p in glob.glob(os.path.join(CACHE, "*-*.pkl"))]
    ranges = [(a, min(a + CHUNK, end)) for a in range(START, end, CHUNK)
              if not any(x <= a and min(a + CHUNK, end) <= y for x, y in done)]
    with Pool(WORKERS) as pool:
        for i, _ in enumerate(pool.imap_unordered(pull, ranges)):
            if i % 25 == 0:
                print(f"{i}/{len(ranges)} slot ranges", file=sys.stderr, flush=True)

    last, rows = {}, 0
    for path in glob.glob(os.path.join(CACHE, "*-*.pkl")):
        n, part = pickle.load(open(path, "rb"))
        rows += n
        for account, v in part.items():
            if account not in last or v[0] >= last[account][0]:
                last[account] = v

    owners = collections.Counter()
    for _, owner, balance in last.values():
        if owner and balance:
            owners[owner] += balance
    held = sum(owners.values())
    one = 10 ** DECIMALS
    print(f"slots {START:,} to {end:,}, {rows:,} balance rows read")
    print(f"token accounts seen       {len(last):,}")
    print(f"wallets with any CASH     {len(owners):,}")
    print(f"wallets with >= $1        {sum(1 for v in owners.values() if v >= one):,}")
    print(f"wallets with >= $10       {sum(1 for v in owners.values() if v >= 10 * one):,}")
    print(f"sum of balances           ${held / one:,.2f}")

    json.dump({"slot": end, "supply": held, "rows": rows, "token_accounts": len(last), "wallets": len(owners),
               "wallets_1": sum(1 for v in owners.values() if v >= one)}, open(os.path.join(HERE, "snapshot.json"), "w"))
    print(f"wrote snapshot.json (supply and slot for script.py)")

    supply = int(post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply", "params": [CASH]}, auth=False)
                 ["result"]["value"]["amount"])
    print(f"Check (RPC getTokenSupply, read now) ${supply / one:,.2f}")
    print(f"  CASH in accounts with no activity since slot {START:,}, or moved since slot {end:,}: "
          f"${(supply - held) / one:,.2f} ({100 * (supply - held) / supply:.2f}% of supply)")

    weekly_holders(end)


WEEK = 1_750_000  # about a week of Solana slots


def weekly_holders(end):
    """Wallets holding at least $1, counted again at the end of each slot range, then sampled about weekly."""
    files = sorted(glob.glob(os.path.join(CACHE, "*-*.pkl")), key=lambda p: int(os.path.basename(p).split("-")[0]))
    last, steps, one = {}, [], 10 ** DECIMALS
    for path in files:
        upto = int(os.path.basename(path)[:-4].split("-")[1])
        _, part = pickle.load(open(path, "rb"))
        for account, v in part.items():
            if account not in last or v[0] >= last[account][0]:
                last[account] = v
        owners = collections.Counter()
        for _, owner, balance in last.values():
            if owner and balance:
                owners[owner] += balance
        steps.append((upto, sum(1 for v in owners.values() if v >= one)))
    points, x = [], end
    while x > steps[0][0]:
        points.append([c for c in steps if c[0] <= x][-1][1])
        x -= WEEK
    points.reverse()
    falls = sum(1 for a, b in zip(points, points[1:]) if b < a)
    adds = [b - a for a, b in zip(points, points[1:])]
    print(f"wallets with >= $1, sampled every {WEEK:,} slots (about a week), {len(points)} points")
    print(f"weeks where the count fell: {falls} of {len(points) - 1}")
    print(f"added in each of the last 8 weeks: {', '.join(f'{a:,}' for a in adds[-8:])}")
    json.dump(points, open(os.path.join(HERE, "weekly_wallets_1.json"), "w"))


if __name__ == "__main__":
    main()
