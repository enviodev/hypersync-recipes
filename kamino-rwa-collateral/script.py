# Real-world collateral on Kamino Lend, and what is borrowed against it, with Envio HyperSync.
# For five Kamino RWA markets it finds every reserve (Solana RPC), reads each reserve's state,
# and gets the live token balance of every reserve's supply vault from HyperSync account_activity.
# The vault balance is the liquidity sitting in the reserve; it must match the reserve's own
# available_amount, which is how the script checks itself.
# Python 3 standard library only. Set ENVIO_API_TOKEN first. SOLANA_RPC is optional.
import base64
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request

HYPERSYNC = "https://solana.hypersync.xyz"
RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
KLEND = "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"
RESERVE_SIZE = 8624

# Kamino lending markets built around a real-world asset, and the asset used as collateral in each.
MARKETS = {
    "47tfyEG9SsdEnUm9cw5kY9BXngQGqu3LBoop9j5uTAv8": ("Reinsurance (OnRe ONyc)", "5Y8NV33Vv7WbnLfq3zBcKSdYPrk7g2KoiQoe7M2tcxp5"),
    "Btu8835QDYgdTnMJJBSidbfQhrZzryZbMhCpty6h6Xdk": ("Car loans (Hastra AUTO)", "GNE6oDS6jHrfaV3GQVVCCp37fDnT7PiPuewMKBj2bqNm"),
    "CqAoLuqWtavaVE8deBjMKe8ZfSt9ghR6Vb8nfsyabyHA": ("Home equity (Hastra PRIME)", "3b8X44fLF9ooXaUm3hhSgjpmVs6rZZ3pPoGnGahc3Uu7"),
    "52FSGeeokLpgvgAMdqxyt5Hoc2TbUYj5b8yxrEdZ37Vf": ("Payments financing (Huma PST)", "59obFNBzyTBGowrkif5uK7ojS58vsuWz3ZCvg6tfZAGw"),
    "CyyFApdfEzHM5dVowALutPiL3fZepMrThtQUed77A1KN": ("Payments financing (Huma PST)", "59obFNBzyTBGowrkif5uK7ojS58vsuWz3ZCvg6tfZAGw"),
}
SYMBOLS = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC", "2u1tszSeqZ3qBWF3uNGPFc8TzMk2tdiwknnRMWGWjGWH": "USDG",
    "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo": "PYUSD", "CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH": "CASH",
    "8fr7WGTVFszfyNWRMXj6fRjZZAnDwmXwEpCrtzmUkdih": "wYLDS", "USDSwr9ApdHk5bvJKMjzff41FfuX8bSxdKcR81vTwcA": "USDS",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT", "AUSD1jCcCyPLybk1YnvPWsHQSrZ46dxwoMniN4N2UEB9": "AUSD",
    "5Y8NV33Vv7WbnLfq3zBcKSdYPrk7g2KoiQoe7M2tcxp5": "ONyc", "GNE6oDS6jHrfaV3GQVVCCp37fDnT7PiPuewMKBj2bqNm": "AUTO",
    "3b8X44fLF9ooXaUm3hhSgjpmVs6rZZ3pPoGnGahc3Uu7": "PRIME", "59obFNBzyTBGowrkif5uK7ojS58vsuWz3ZCvg6tfZAGw": "PST",
}

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58(raw):
    n, out = int.from_bytes(raw, "big"), ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return "1" * (len(raw) - len(raw.lstrip(b"\0"))) + out


def post(url, body, headers):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    for attempt in range(30):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e:
            # HyperSync says how long until the rate-limit window resets
            wait = int(e.headers.get("x-ratelimit-reset") or 0) if e.code == 429 else 0
            print(f"  HTTP {e.code}, retrying in {max(wait, 3)}s", file=sys.stderr)
            time.sleep(max(wait, 3 * min(attempt + 1, 5)))
        except Exception as e:
            print(f"  retrying after {type(e).__name__}", file=sys.stderr)
            time.sleep(3 * min(attempt + 1, 5))
    sys.exit("request kept failing: " + url)


def rpc(method, params):
    return post(RPC, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, {})["result"]


def hypersync(body):
    return post(HYPERSYNC + "/query", body, {"Authorization": "Bearer " + TOKEN})


def reserves_of(market):
    """Every Kamino reserve account whose lending_market (offset 32) is this market."""
    accts = rpc("getProgramAccounts", [KLEND, {"encoding": "base64", "dataSlice": {"offset": 0, "length": 0},
                                              "filters": [{"dataSize": RESERVE_SIZE}, {"memcmp": {"offset": 32, "bytes": market}}]}])
    return [a["pubkey"] for a in accts]


def decode(data):
    """ReserveLiquidity fields from a Kamino Reserve account."""
    d = base64.b64decode(data)
    dec = struct.unpack_from("<Q", d, 272)[0]
    return {
        "mint": b58(d[128:160]),
        "vault": b58(d[160:192]),
        "available": struct.unpack_from("<Q", d, 224)[0] / 10**dec,
        "borrowed": int.from_bytes(d[232:248], "little") / 2**60 / 10**dec,  # borrowed_amount_sf, a 60-bit fixed-point number
        "price": int.from_bytes(d[248:264], "little") / 2**60,  # market_price_sf, USD per token
        "decimals": dec,
    }


def vault_balances(vaults, head):
    """Latest token balance of each vault from HyperSync account_activity, walking back from the chain head."""
    found, to, step = {}, head, 25_000
    while len(found) < len(vaults) and head - to < 1_300_000:  # up to about 6 days of slots
        todo = [v for v in vaults if v not in found]
        body = {"from_slot": to - step, "to_slot": to, "account_activity": [{"account": todo}],
                "field_selection": {"account_activity": ["slot", "account", "post_token_balance", "token_decimals"]}}
        while body["from_slot"] < to:
            res = hypersync(body)
            for b in res.get("account_activity") or []:
                for r in b:
                    if r.get("post_token_balance") is None:
                        continue
                    prev = found.get(r["account"])
                    if prev is None or r["slot"] >= prev[0]:
                        found[r["account"]] = (r["slot"], int(r["post_token_balance"]) / 10**r["token_decimals"])
            if res["next_slot"] <= body["from_slot"]:
                break
            body["from_slot"] = res["next_slot"]
        to -= step
        print(f"  HyperSync: {len(found)} of {len(vaults)} vaults found, {head - to:,} slots back", file=sys.stderr)
    return {v: bal for v, (slot, bal) in found.items()}


head = json.load(urllib.request.urlopen(HYPERSYNC + "/height"))
reserves = []
for market, (label, rwa_mint) in MARKETS.items():
    keys = reserves_of(market)
    for acct in rpc("getMultipleAccounts", [keys, {"encoding": "base64"}])["value"]:
        r = decode(acct["data"][0])
        r.update(label=label, rwa_mint=rwa_mint, supplied=(r["available"] + r["borrowed"]) * r["price"])
        if r["supplied"] >= 1_000_000:
            reserves.append(r)
balances = vault_balances([r["vault"] for r in reserves], head)

collateral, borrowed, flows = {}, {}, {}
for r in reserves:
    hs = balances.get(r["vault"])
    check = "matches" if hs is not None and abs(hs - r["available"]) < 1e-6 * max(1, r["available"]) else f"HyperSync {hs}"
    sym = SYMBOLS.get(r["mint"], r["mint"][:6])
    usd_borrowed = r["borrowed"] * r["price"]
    print(f"{r['label']:32} {sym:7} supplied ${r['supplied'] / 1e6:7.2f}M  borrowed ${usd_borrowed / 1e6:7.2f}M  vault {check}")
    if r["mint"] == r["rwa_mint"]:
        collateral[r["label"]] = collateral.get(r["label"], 0) + r["supplied"]
    elif usd_borrowed >= 1_000_000:  # reserves with at least $1M borrowed
        borrowed[sym] = borrowed.get(sym, 0) + usd_borrowed
        flows[(r["label"], sym)] = flows.get((r["label"], sym), 0) + usd_borrowed

print("\nReal-world collateral")
for label, usd in sorted(collateral.items(), key=lambda x: -x[1]):
    print(f"  {label:32} ${usd / 1e6:7.1f}M")
print(f"  {'Total':32} ${sum(collateral.values()) / 1e6:7.1f}M")
print("\nBorrowed against it")
for sym, usd in sorted(borrowed.items(), key=lambda x: -x[1]):
    print(f"  {sym:32} ${usd / 1e6:7.1f}M")
print(f"  {'Total':32} ${sum(borrowed.values()) / 1e6:7.1f}M")
json.dump({"collateral": collateral, "borrowed": borrowed, "flows": [[a, b, v] for (a, b), v in flows.items()]},
          open("kamino_rwa.json", "w"), indent=1)
