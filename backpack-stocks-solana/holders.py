"""Who holds Backpack's tokenized stocks on Solana right now, and how much.

For each of the 94 mints in mints.json this reads every Token-2022 account over Solana RPC
(getProgramAccounts), prices the balances with Jupiter's price API, and counts wallets.
It checks every mint's balances against the supply stored on the mint account.

Usage:
    python holders.py
    SOLANA_RPC=https://your-rpc python holders.py     # the public RPC is slow and rate limited
"""
import base64, collections, json, os, time, urllib.request

RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
T22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
HERE = os.path.dirname(os.path.abspath(__file__))
MINTS = json.load(open(os.path.join(HERE, "mints.json")))
DECIMALS = 6


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(15):
        try:
            req = urllib.request.Request(RPC, body, {"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=120))
            if "result" in r:
                return r["result"]
        except Exception:
            pass
        time.sleep(4 * (attempt + 1))  # rate limited: wait and retry
    raise SystemExit(f"{method} kept failing")


def prices(mints):
    out = {}
    for i in range(0, len(mints), 50):
        url = "https://lite-api.jup.ag/price/v3?ids=" + ",".join(mints[i:i + 50])
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        for mint, v in json.load(urllib.request.urlopen(req, timeout=30)).items():
            out[mint] = v["usdPrice"]
    return out


def main():
    px = prices(list(MINTS.values()))
    mint_accounts = rpc("getMultipleAccounts", [list(MINTS.values()), {"encoding": "jsonParsed"}])["value"]
    supply = {t: int(a["data"]["parsed"]["info"]["supply"]) for t, a in zip(MINTS, mint_accounts)}
    wallet_usd = collections.defaultdict(float)
    rows = []
    for ticker, mint in MINTS.items():
        # token account layout: mint 0..32, owner 32..64, amount 64..72
        accounts = rpc("getProgramAccounts", [T22, {"encoding": "base64", "dataSlice": {"offset": 32, "length": 40},
                                                    "filters": [{"memcmp": {"offset": 0, "bytes": mint}}]}])
        owners = collections.Counter()
        for a in accounts:
            raw = base64.b64decode(a["account"]["data"][0])
            amount = int.from_bytes(raw[32:40], "little")
            if amount:
                owners[raw[:32]] += amount
        p = px[mint]
        for owner, amount in owners.items():
            wallet_usd[owner] += amount / 10**DECIMALS * p
        held = sum(owners.values())
        rows.append((ticker, held / 10**DECIMALS * p, sum(1 for v in owners.values() if v / 10**DECIMALS * p >= 1),
                     len(owners), held, supply[ticker]))
        time.sleep(2)
    rows.sort(key=lambda r: -r[1])
    print("ticker      value   wallets $1+  wallets any  balances / supply")
    for ticker, usd, w1, w, held, sup in rows:
        print(f"{ticker:<6} ${usd:>12,.0f} {w1:>9,} {w:>12,}  {held / sup:.4%}")
    print(f"\ntokens                    {len(rows)}")
    print(f"value held                ${sum(r[1] for r in rows):,.0f}")
    print(f"wallets holding any       {len(wallet_usd):,}")
    for cut in (1, 10, 100, 1000):
        print(f"wallets holding ${cut}+{' ' * (9 - len(str(cut)))}{sum(1 for v in wallet_usd.values() if v >= cut):,}")


if __name__ == "__main__":
    main()
