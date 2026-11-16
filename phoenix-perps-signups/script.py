# Every trading account opened and every USDC deposit made on Phoenix, the perps exchange on Solana,
# with Envio HyperSync. Pulls the RegisterTrader and DepositFunds instructions of the Phoenix program,
# counts distinct wallets and adds up the deposits, month by month.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import concurrent.futures
import datetime
import json
import os
import struct
import sys
import threading
import time
import urllib.error
import urllib.request

HYPERSYNC = "https://solana.hypersync.xyz"
# Program ID and instruction discriminators from Phoenix's public SDK, https://github.com/Ellipsis-Labs/rise-public
PHOENIX = "EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih"
REGISTER_TRADER = "4bf3e0a701053320"  # accounts: ..., a4 = the trader's wallet, a5 = the new trader account
DEPOSIT_FUNDS = "ca2734d33514fa58"    # accounts: ..., a3 = the trader's wallet. Data: u64 USDC amount after the discriminator
FIRST_SLOT = 391_001_451  # 3 Jan 2026, the start of HyperSync's Solana history
SEGMENT = 1_000_000       # slots per parallel segment
WORKERS = 16

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def post(body):
    req = urllib.request.Request(HYPERSYNC + "/query", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(40):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("x-ratelimit-reset") or 0) if e.code == 429 else 0
            time.sleep(max(wait, 3) + 1)
        except Exception:
            time.sleep(3 * min(attempt + 1, 5))
    sys.exit("request kept failing")


start = int(sys.argv[1]) if len(sys.argv) > 1 else FIRST_SLOT
head = int(sys.argv[2]) if len(sys.argv) > 2 else json.load(urllib.request.urlopen(HYPERSYNC + "/height"))
lock = threading.Lock()
rows = {}  # (slot, transaction index, instruction address) -> (block time, kind, wallet, amount)


def pull(segment):
    a, b = segment
    body = {
        "from_slot": a, "to_slot": b,
        "instruction_calls": [{"executing_account": [PHOENIX], "d8": [REGISTER_TRADER, DEPOSIT_FUNDS], "tx_success": True}],
        "field_selection": {"instruction_call": ["slot", "transaction_index", "instruction_address", "d8", "data", "a3", "a4"],
                            "block": ["slot", "block_time"]},
    }
    while True:
        res = post(body)
        times = {blk["slot"]: blk["block_time"] for batch in res.get("blocks") or [] for blk in batch}
        with lock:
            for batch in res.get("instruction_calls") or []:
                for r in batch:
                    key = (r["slot"], r["transaction_index"], str(r["instruction_address"]))
                    if r["d8"] == REGISTER_TRADER:
                        rows[key] = (times[r["slot"]], "register", r["a4"], 0)
                    else:
                        amount = struct.unpack_from("<Q", bytes.fromhex(r["data"]), 8)[0]
                        rows[key] = (times[r["slot"]], "deposit", r["a3"], amount)
        if res["next_slot"] >= b or res["next_slot"] <= body["from_slot"]:
            return
        body["from_slot"] = res["next_slot"]


segments = [(a, min(a + SEGMENT, head)) for a in range(start, head, SEGMENT)]
with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
    for i, _ in enumerate(pool.map(pull, segments), 1):
        print(f"  segment {i} of {len(segments)}", file=sys.stderr)

month = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m")
day = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d")
wallets, depositors, deposited = set(), set(), 0
new_by_month, usdc_by_month, new_by_day = collections.Counter(), collections.Counter(), collections.Counter()
registrations = deposits = 0
for t, kind, wallet, amount in sorted(rows.values()):
    if kind == "register":
        registrations += 1
        if wallet not in wallets:
            wallets.add(wallet)
            new_by_month[month(t)] += 1
            new_by_day[day(t)] += 1
    else:
        deposits += 1
        depositors.add(wallet)
        deposited += amount
        usdc_by_month[month(t)] += amount

print(f"{'month':8} {'new wallets':>12} {'all wallets':>12} {'USDC deposited':>16}")
running = 0
for m in sorted(set(new_by_month) | set(usdc_by_month)):
    running += new_by_month[m]
    print(f"{m:8} {new_by_month[m]:12,} {running:12,} {usdc_by_month[m] / 1e6:16,.0f}")
print(f"\nSlots {start:,} to {head:,}")
print(f"RegisterTrader instructions: {registrations:,}")
print(f"Wallets that opened a trading account: {len(wallets):,}")
print(f"DepositFunds instructions: {deposits:,}")
print(f"Wallets that deposited: {len(depositors):,}")
print(f"USDC deposited: ${deposited / 1e6:,.0f}")
json.dump({"new_wallets_by_day": dict(sorted(new_by_day.items())), "slots": [start, head]},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "signups_by_day.json"), "w"))
