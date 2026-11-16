# Every raise funded through MetaDAO's launchpad on Solana, with Envio HyperSync.
# Pulls every instruction run by MetaDAO's launchpad programs, decodes initialize_launch, fund and
# complete_launch, and adds up what each completed raise asked for and what people committed.
# It then reads every Launch account over Solana RPC and checks that the account holds the same total.
# Python 3 standard library only. Set ENVIO_API_TOKEN first. SOLANA_RPC is optional.
import base64
import collections
import datetime
import hashlib
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request

HYPERSYNC = "https://solana.hypersync.xyz"
RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
# Launchpad program IDs from https://github.com/metaDAOproject/programs#deployments
PROGRAMS = [
    "moonDJUoHteKkGATejA5bdJVwJ6V6Dg74gyqyJTx73n",  # v0.8.0
    "moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM",  # v0.7.0
    "MooNyh4CBUYEKyXVnjGYQ8mEiJDpGvJMdvrZx1iGeHV",  # v0.6.0
    "mooNhciQJi1LqHDmse2JPic2NqG2PXCanbE3ZYzP3qA",  # v0.5.0
    "AfJJJ5UqxhBKoE3grkKAZZsoXDE9kncbMKvqSHGsCNrE",  # v0.4.1
]
FIRST_SLOT = 391_001_451  # 3 Jan 2026, the start of HyperSync's Solana history
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
MIN_WALLETS = 10  # leave out test launches, which have a handful of wallets and goals of a few dollars

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def disc(name):
    """Anchor instruction discriminator: the first 8 bytes of sha256('global:<name>')."""
    return hashlib.sha256(("global:" + name).encode()).digest()[:8].hex()


INIT, FUND, COMPLETE = disc("initialize_launch"), disc("fund"), disc("complete_launch")


def post(url, body, headers):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    for attempt in range(40):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("x-ratelimit-reset") or 0) if e.code == 429 else 0
            print(f"  HTTP {e.code}, retrying in {max(wait, 5)}s", file=sys.stderr)
            time.sleep(max(wait, 5) + 1)
        except Exception as e:
            print(f"  retrying after {type(e).__name__}", file=sys.stderr)
            time.sleep(3 * min(attempt + 1, 5))
    sys.exit("request kept failing: " + url)


def launch_args(data):
    """minimum_raise_amount and token name from initialize_launch's arguments."""
    b = bytes.fromhex(data)
    goal = struct.unpack_from("<Q", b, 8)[0]
    try:
        members = struct.unpack_from("<I", b, 24)[0]
        at = 28 + 32 * members + 4  # skip the spending-limit members and seconds_for_launch
        n = struct.unpack_from("<I", b, at)[0]
        name = b[at + 4:at + 4 + n].decode()
    except Exception:
        name = "?"
    return goal, name


start = int(sys.argv[1]) if len(sys.argv) > 1 else FIRST_SLOT
head = int(sys.argv[2]) if len(sys.argv) > 2 else json.load(urllib.request.urlopen(HYPERSYNC + "/height"))
body = {
    "from_slot": start, "to_slot": head,
    "instruction_calls": [{"executing_account": PROGRAMS}],
    "field_selection": {"instruction_call": ["slot", "transaction_index", "instruction_address", "executing_account",
                                             "data", "tx_success", "a0", "a1", "a3", "a4", "a6", "a7"],
                        "block": ["slot", "block_time"]},
}
seen, block_time = set(), {}
launches, completed = {}, set()
funds = collections.defaultdict(lambda: {"raw": 0, "funders": set(), "first_slot": None})
while True:
    res = post(HYPERSYNC + "/query", body, {"Authorization": "Bearer " + TOKEN})
    for batch in res.get("blocks") or []:
        for b in batch:
            block_time[b["slot"]] = b.get("block_time")
    for batch in res.get("instruction_calls") or []:
        for r in batch:
            key = (r["slot"], r["transaction_index"], str(r["instruction_address"]))
            if key in seen or r.get("tx_success") is False or r["executing_account"] not in PROGRAMS:
                continue
            seen.add(key)
            data = r["data"][2:] if r["data"].startswith("0x") else r["data"]
            kind, launch = data[:16], r["a0"]
            if kind == INIT:
                launches[launch] = launch_args(data)
            elif kind == COMPLETE:
                completed.add(launch)
            elif kind == FUND:
                # the funder sits one account later in the older fund layout, which has a launch signer before it
                funder = r["a4"] if r["a7"] == TOKEN_PROGRAM else r["a3"]
                f = funds[launch]
                f["raw"] += struct.unpack_from("<Q", bytes.fromhex(data), 8)[0]
                f["funders"].add(funder)
                f["first_slot"] = f["first_slot"] or r["slot"]
    print(f"  slot {res['next_slot']:,} of {head:,}", file=sys.stderr)
    if res["next_slot"] >= head or res["next_slot"] <= body["from_slot"]:
        break
    body["from_slot"] = res["next_slot"]
    time.sleep(0.25)  # stay well inside the rate limit

raises = [k for k in completed if k in funds and k in launches and len(funds[k]["funders"]) >= MIN_WALLETS]
raises.sort(key=lambda k: -funds[k]["raw"])

# Check: each Launch account stores its total committed amount as a u64. Look for our sum in the account data.
accounts = []
for i in range(0, len(raises), 100):
    accounts += post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "getMultipleAccounts",
                           "params": [raises[i:i + 100], {"encoding": "base64"}]}, {})["result"]["value"]
matched = 0
print(f"{'raise':22} {'first commitment':17} {'goal':>12} {'committed':>14} {'x goal':>7} {'wallets':>8}  onchain total")
for k, acct in zip(raises, accounts):
    goal, name = launches[k]
    f = funds[k]
    ok = acct is not None and struct.pack("<Q", f["raw"]) in base64.b64decode(acct["data"][0])
    matched += ok
    day = datetime.datetime.fromtimestamp(block_time[f["first_slot"]], datetime.timezone.utc).strftime("%Y-%m-%d")
    print(f"{name[:22]:22} {day:17} {goal / 1e6:12,.0f} {f['raw'] / 1e6:14,.0f} {f['raw'] / goal:7.1f} {len(f['funders']):8,}  "
          f"{'matches' if ok else 'differs or closed'}")

total = sum(funds[k]["raw"] for k in raises) / 1e6
goals = sum(launches[k][0] for k in raises) / 1e6
wallets = set().union(*[funds[k]["funders"] for k in raises]) if raises else set()
print(f"\nSlots {start:,} to {head:,}")
print(f"Completed raises with 10 or more wallets: {len(raises)}")
print(f"Goals, added up: ${goals:,.0f}")
print(f"Committed:       ${total:,.0f} ({total / goals:.1f}x the goals)")
print(f"Wallets that committed: {len(wallets):,}")
print(f"Launch accounts whose onchain total matches: {matched} of {len(raises)}")
