"""Every Phantom CASH mint and burn on Solana, pulled with Envio HyperSync.

CASH is a Token-2022 stablecoin. Its mint, from Phantom's docs (https://docs.phantom.com/cash):
CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH

The script pulls every successful MintTo / MintToChecked (account 0 is the mint) and
Burn / BurnChecked (account 1 is the mint) instruction on the Token-2022 program, outer and inner,
from FROM_SLOT to the chain head. It then reads the live supply over RPC with getTokenSupply and
works back to the supply at the start of the window, so you can see how it changed week by week.

Usage:
    export ENVIO_API_TOKEN=your-token
    python script.py                 # from slot 391,000,000 (3 Jan 2026), the start of HyperSync's Solana history
    FROM_SLOT=440000000 python script.py
"""
import collections, datetime, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

HS = "https://solana.hypersync.xyz"
RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (https://envio.dev/app/api-tokens)")
T22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
CASH = "CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH"
DECIMALS = 6
FROM_SLOT = int(os.environ.get("FROM_SLOT", 391_000_000))
WORKERS = int(os.environ.get("WORKERS", 8))
CHUNK = 5_000_000


def post(url, body, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    for attempt in range(40):
        try:
            req = urllib.request.Request(url, json.dumps(body).encode(), headers)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception as e:  # 429s and timeouts: back off and retry
            print("retry:", e, file=sys.stderr)
            time.sleep(min(30, 2 * (attempt + 1)))
    sys.exit("HyperSync kept failing")


def pull(a, b):
    """Every CASH mint and burn in [a, b). Raises rather than returning a partial range."""
    sel = [
        {"executing_account": [T22], "d1": ["07", "0e"], "a0": [CASH], "tx_success": True},  # MintTo, MintToChecked
        {"executing_account": [T22], "d1": ["08", "0f"], "a1": [CASH], "tx_success": True},  # Burn, BurnChecked
    ]
    body = {"from_slot": a, "to_slot": b, "instruction_calls": sel,
            "field_selection": {"instruction_call": ["slot", "d1", "data"], "block": ["slot", "block_time"]}}
    rows, stalls = [], 0
    while body["from_slot"] < b:
        r = post(HS + "/query", body)
        times = {x["slot"]: x.get("block_time") for batch in r.get("blocks") or [] for x in batch}
        for batch in r.get("instruction_calls") or []:
            for x in batch:
                amount = int.from_bytes(bytes.fromhex(x["data"][2:18]), "little")
                kind = "mint" if x["d1"] in ("07", "0e") else "burn"
                rows.append((x["slot"], times.get(x["slot"]), kind, amount))
        if r["next_slot"] <= body["from_slot"]:
            stalls += 1
            if stalls > 20:
                raise RuntimeError(f"no progress at slot {body['from_slot']}")
            time.sleep(2)
            continue
        stalls = 0
        body["from_slot"] = r["next_slot"]
    return rows


def main():
    head = int(urllib.request.urlopen(HS + "/height").read())
    ranges = [(a, min(a + CHUNK, head)) for a in range(FROM_SLOT, head, CHUNK)]
    with ThreadPoolExecutor(WORKERS) as ex:
        rows = sorted(r for part in ex.map(lambda ab: pull(*ab), ranges) for r in part)
    minted = sum(a for _, _, k, a in rows if k == "mint")
    burned = sum(a for _, _, k, a in rows if k == "burn")
    supply = int(post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply", "params": [CASH]}, auth=False)
                 ["result"]["value"]["amount"])
    start = supply - (minted - burned)
    usd = lambda raw: raw / 10**DECIMALS
    print(f"slots {FROM_SLOT:,} to {head:,}")
    print(f"mints {sum(1 for r in rows if r[2]=='mint'):,}  burns {sum(1 for r in rows if r[2]=='burn'):,}")
    print(f"minted ${usd(minted):,.2f}  burned ${usd(burned):,.2f}  net ${usd(minted-burned):,.2f}")
    print(f"supply now (RPC getTokenSupply) ${usd(supply):,.2f}")
    print(f"supply at slot {FROM_SLOT:,} (now minus net) ${usd(start):,.2f}")
    # supply at the end of each ISO week
    weekly, s = collections.OrderedDict(), start
    for slot, ts, kind, amount in rows:
        s += amount if kind == "mint" else -amount
        if ts:
            d = datetime.datetime.fromtimestamp(ts, datetime.UTC).date()
            weekly[d - datetime.timedelta(days=d.weekday())] = s
    print("\nweek of     supply at week end")
    for wk, v in weekly.items():
        print(f"{wk}  ${usd(v):,.0f}")
    json.dump({"from_slot": FROM_SLOT, "head": head, "rows": rows, "supply_now": supply}, open("cash_mint_burn.json", "w"))


if __name__ == "__main__":
    main()
