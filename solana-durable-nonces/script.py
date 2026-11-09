# Durable nonce transactions on Solana, with Envio HyperSync.
# Counts every successful transaction whose first instruction is System Program AdvanceNonceAccount,
# per UTC day, with the distinct nonce accounts and fee payers behind them,
# then samples all successful non-vote transactions to estimate their share.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import itertools
import json
import os
import random
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

HYPERSYNC = "https://solana.hypersync.xyz"
SYSTEM_PROGRAM = "11111111111111111111111111111111"
ADVANCE_NONCE = "04000000"  # SystemInstruction::AdvanceNonceAccount, a little-endian u32 of 4
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def query(body):
    req = urllib.request.Request(HYPERSYNC + "/query", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(12):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:
            time.sleep(2 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def block_time(slot):
    res = query({"from_slot": slot, "to_slot": slot + 40, "include_all_blocks": True,
                 "field_selection": {"block": ["slot", "block_time"]}})
    return next(b["block_time"] for batch in res["blocks"] for b in batch if b.get("block_time"))


def first_slot_at(ts, lo, hi):
    """First slot whose block_time is at or after ts."""
    while hi - lo > 50:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if block_time(mid) < ts else (lo, mid)
    res = query({"from_slot": lo, "to_slot": hi + 40, "include_all_blocks": True,
                 "field_selection": {"block": ["slot", "block_time"]}})
    return min(b["slot"] for batch in res["blocks"] for b in batch if b.get("block_time", 0) >= ts)


NONCE_FILTER = [{"executing_account": [SYSTEM_PROGRAM], "d4": [ADVANCE_NONCE], "is_inner": False}]


def nonce_txs(start, end):
    """Count, nonce accounts and fee payers of the transactions in [start, end) that open with AdvanceNonceAccount."""
    body = {"from_slot": start, "to_slot": end, "instruction_calls": NONCE_FILTER,
            "field_selection": {"instruction_call": ["slot", "transaction_index", "instruction_address", "data", "a0"],
                                "transaction": ["slot", "transaction_index", "fee_payer"]}}
    count, accounts, payers = 0, set(), Counter()
    while body["from_slot"] < end:
        res = query(body)
        payer = {(t["slot"], t["transaction_index"]): t["fee_payer"]
                 for batch in res.get("transactions") or [] for t in batch}
        for batch in res.get("instruction_calls") or []:
            for ix in batch:
                # Durable nonce transactions must put AdvanceNonceAccount first, at instruction_address [0]
                if ix.get("data") == ADVANCE_NONCE and ix["instruction_address"] == [0]:
                    count += 1
                    accounts.add(ix["a0"])  # account 0 of AdvanceNonceAccount is the nonce account
                    payers[payer[(ix["slot"], ix["transaction_index"])]] += 1
        if res["next_slot"] <= body["from_slot"]:
            break
        body["from_slot"] = res["next_slot"]
    return count, accounts, payers


def sample_share(start, end, windows=48, width=20):
    """Successful non-vote transactions and nonce transactions in random 20-slot windows of one day."""
    total = nonce = 0
    for s in random.sample(range(start, end - width), windows):
        res = query({"from_slot": s, "to_slot": s + width, "transactions": [{"success": True}],
                     "field_selection": {"transaction": ["slot"]}, "max_num_transactions": 100000})
        total += sum(len(b) for b in res.get("transactions") or [])
        res = query({"from_slot": s, "to_slot": s + width, "instruction_calls": NONCE_FILTER,
                     "field_selection": {"instruction_call": ["instruction_address", "data"]}})
        nonce += sum(1 for b in res.get("instruction_calls") or [] for ix in b
                     if ix.get("data") == ADVANCE_NONCE and ix["instruction_address"] == [0])
    return total, nonce


# Find the first slot of each UTC day in the window.
height = json.load(urllib.request.urlopen(HYPERSYNC + "/height"))
today = datetime.datetime.now(datetime.timezone.utc).date()
days = [today - datetime.timedelta(d) for d in range(DAYS, -1, -1)]
bounds, lo = {}, height - 450_000 * (DAYS + 3)
for d in days:
    ts = int(datetime.datetime.combine(d, datetime.time(), datetime.timezone.utc).timestamp())
    bounds[d] = lo = first_slot_at(ts, lo, height)
days = days[:-1]  # the last bound is today's start; only complete days are counted
end_of = {d: bounds[d + datetime.timedelta(1)] for d in days}

chunks = [(d, s, min(s + 20_000, end_of[d])) for d in days for s in range(bounds[d], end_of[d], 20_000)]
print(f"Reading {len(chunks)} slot ranges from HyperSync...", file=sys.stderr)
with ThreadPoolExecutor(24) as pool:
    parts = list(pool.map(lambda c: (c[0], nonce_txs(c[1], c[2])), chunks))

random.seed(7)
with ThreadPoolExecutor(10) as pool:
    shares = dict(zip(days, pool.map(lambda d: sample_share(bounds[d], end_of[d]), days)))

per_day = defaultdict(lambda: [0, set(), set()])
all_accounts, payers = set(), Counter()
for d, (count, accounts, chunk_payers) in parts:
    per_day[d][0] += count
    per_day[d][1] |= accounts
    per_day[d][2] |= set(chunk_payers)
    all_accounts |= accounts
    payers.update(chunk_payers)

print(f"{'Day':<12}{'Nonce txs':>12}{'Nonce accts':>13}{'Fee payers':>12}{'Share':>8}")
for d in days:
    count, accounts, day_payers = per_day[d]
    total, nonce = shares[d]
    print(f"{d:%d %b}".ljust(12) + f"{count / 1e6:11.2f}M{len(accounts) / 1e3:12.1f}k"
          f"{len(day_payers) / 1e3:11.1f}k{nonce / total:8.1%}")

running = list(itertools.accumulate(v for _, v in payers.most_common()))
print(f"\n{DAYS} days: {running[-1] / 1e6:.1f}M nonce transactions, "
      f"{len(all_accounts) / 1e3:.0f}k nonce accounts, {len(payers) / 1e3:.0f}k fee payers")
print(f"Share of successful non-vote transactions (sampled): "
      f"{sum(n for _, n in shares.values()) / sum(t for t, _ in shares.values()):.1%}")
print(f"Fee payers behind 90% of them: {next(i + 1 for i, c in enumerate(running) if c >= 0.9 * running[-1])}")
