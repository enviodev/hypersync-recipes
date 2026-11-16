"""Every mint and burn of Backpack's tokenized stocks on Solana, pulled with Envio HyperSync.

Backpack Securities issues 94 stocks and ETFs as Token-2022 tokens on Solana. The mints in mints.json
come from Backpack's own directory: https://backpack.exchange/tokenized-stocks/assets

A share is tokenized with MintTo / MintToChecked (account 0 is the mint) and leaves the chain with
Burn / BurnChecked (account 1 is the mint). This script pulls both for all 94 mints over the last
DAYS days (default 7), outer and inner calls, successful transactions only, and prints the count
and the number of shares per ticker.

Usage:
    export ENVIO_API_TOKEN=your-token
    python script.py
    DAYS=1 python script.py
"""
import collections, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

HS = "https://solana.hypersync.xyz"
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (https://envio.dev/app/api-tokens)")
T22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
HERE = os.path.dirname(os.path.abspath(__file__))
MINTS = json.load(open(os.path.join(HERE, "mints.json")))  # ticker -> mint
TICKER = {mint: ticker for ticker, mint in MINTS.items()}
DECIMALS = 6
DAYS = float(os.environ.get("DAYS", 7))
SLOTS_PER_DAY = 216_000  # at 400ms a slot; the script filters on block time afterwards
WORKERS = int(os.environ.get("WORKERS", 8))
CHUNK = 100_000


def post(body):
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}
    for attempt in range(40):
        try:
            req = urllib.request.Request(HS + "/query", json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception as e:  # 429s and timeouts: back off and retry
            print("retry:", e, file=sys.stderr)
            time.sleep(min(30, 2 * (attempt + 1)))
    sys.exit("HyperSync kept failing")


def pull(a, b):
    """Every stock-token mint and burn in [a, b)."""
    mints = list(MINTS.values())
    sel = [
        {"executing_account": [T22], "d1": ["07", "0e"], "a0": mints, "tx_success": True},  # MintTo, MintToChecked
        {"executing_account": [T22], "d1": ["08", "0f"], "a1": mints, "tx_success": True},  # Burn, BurnChecked
    ]
    body = {"from_slot": a, "to_slot": b, "instruction_calls": sel,
            "field_selection": {"instruction_call": ["slot", "d1", "data", "a0", "a1"], "block": ["slot", "block_time"]}}
    rows = []
    while body["from_slot"] < b:
        r = post(body)
        times = {x["slot"]: x.get("block_time") for batch in r.get("blocks") or [] for x in batch}
        for batch in r.get("instruction_calls") or []:
            for x in batch:
                kind = "mint" if x["d1"] in ("07", "0e") else "burn"
                mint = x["a0"] if kind == "mint" else x["a1"]
                amount = int.from_bytes(bytes.fromhex(x["data"][2:18]), "little")
                rows.append((x["slot"], times.get(x["slot"]), kind, TICKER[mint], amount))
        if r["next_slot"] <= body["from_slot"]:
            time.sleep(2)
            continue
        body["from_slot"] = r["next_slot"]
    return rows


def main():
    head = int(urllib.request.urlopen(HS + "/height").read())
    start = head - int(DAYS * SLOTS_PER_DAY * 1.3)  # slots are often faster than 400ms, so start early
    ranges = [(a, min(a + CHUNK, head)) for a in range(start, head, CHUNK)]
    with ThreadPoolExecutor(WORKERS) as ex:
        rows = sorted(r for part in ex.map(lambda ab: pull(*ab), ranges) for r in part)
    newest = max(r[1] for r in rows if r[1])
    cutoff = newest - DAYS * 86400
    rows = [r for r in rows if r[1] and r[1] >= cutoff]
    by = collections.defaultdict(lambda: {"mint": [0, 0], "burn": [0, 0]})
    for _, _, kind, ticker, amount in rows:
        by[ticker][kind][0] += 1
        by[ticker][kind][1] += amount
    n_mint = sum(v["mint"][0] for v in by.values())
    n_burn = sum(v["burn"][0] for v in by.values())
    print(f"last {DAYS:g} days, slots {rows[0][0]:,} to {rows[-1][0]:,}")
    print(f"mints {n_mint:,}  burns {n_burn:,}  tickers with activity {len(by)} of {len(MINTS)}")
    print("\nticker   mints  shares minted   burns  shares burned")
    for ticker, v in sorted(by.items(), key=lambda kv: -(kv[1]["mint"][0] + kv[1]["burn"][0])):
        print(f"{ticker:<6} {v['mint'][0]:>7,} {v['mint'][1] / 10**DECIMALS:>14,.2f} {v['burn'][0]:>7,} {v['burn'][1] / 10**DECIMALS:>14,.2f}")
    json.dump(rows, open(os.path.join(HERE, "stock_mint_burn.json"), "w"))


if __name__ == "__main__":
    main()
