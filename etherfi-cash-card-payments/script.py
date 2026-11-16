"""Every ether.fi Cash card payment on Optimism, from the Spend event.

ether.fi Cash settles each card payment onchain on OP Mainnet. The CashModule
calls the CashEventEmitter, which emits one Spend event per payment with the
user's safe, the payment id, the card issuer (bin sponsor), the tokens spent
and the total USD amount. This script reads every Spend event in a window with
Envio HyperSync and prints payments per day, distinct paying safes, USD spent,
the median payment and the share of payments under $100.

It also gives each cardholder (one ether.fi safe) a typical payment, the median
of their own payments, so a handful of very busy accounts can't skew the answer,
and counts how many cardholders paid on every day of the window.

Usage:  ENVIO_API_TOKEN=... python3 script.py [START END]
        START and END are UTC dates (YYYY-MM-DD), both included.
        Default: the last 7 full UTC days.
"""
import collections, datetime, json, os, statistics, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN")
HS = "https://optimism.hypersync.xyz"
# ether.fi Cash v3 on Optimism (docs: Deployed Contracts page, repo etherfi-protocol/cash-v3)
EMITTER = "0x380b2e96799405be6e3d965f4044099891881acb"  # CashEventEmitter
# Spend(address indexed safe, bytes32 indexed txId, BinSponsor indexed binSponsor,
#       address[] tokens, uint256[] amounts, uint256[] amountInUsd, uint256 totalUsdAmt, Mode mode)
SPEND = "0x244f4cc0665ad7ee4709aa59b30d3ea581cecde1b0430a3f23a5dc609d4890fc"
SPONSORS = ["Reap", "Rain", "PIX", "CardOrder"]  # enum BinSponsor in ICashModule.sol
MODES = ["Credit", "Debit"]                      # enum Mode in ICashModule.sol
UTC = datetime.timezone.utc
if len(sys.argv) == 3:
    START, END = (datetime.datetime.strptime(a, "%Y-%m-%d").replace(tzinfo=UTC) for a in sys.argv[1:3])
else:
    today = datetime.datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    START, END = today - datetime.timedelta(days=7), today - datetime.timedelta(days=1)
T0, T1 = START.timestamp(), (END + datetime.timedelta(days=1)).timestamp()
BLOCKS_PER_DAY = 43_200  # OP Mainnet makes a block every 2 seconds
THREADS = 4


def call(path, body=None):
    for attempt in range(30):
        try:
            req = urllib.request.Request(HS + path, json.dumps(body).encode() if body else None,
                                         {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(min(30, 3 * (attempt + 1)))
    raise SystemExit("HyperSync request failed")


def word(data, i):
    return int(data[2 + 64 * i: 2 + 64 * (i + 1)], 16)


def pull(rng):
    a, b = rng
    out, ts = [], {}
    body = {"from_block": a, "to_block": b,
            "logs": [{"address": [EMITTER], "topics": [[SPEND]]}],
            "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "topic3", "data", "block_number"],
                                "block": ["number", "timestamp"]}}
    while True:
        r = call("/query", body)
        for batch in r["data"]:
            for blk in batch.get("blocks") or []:
                t = blk["timestamp"]
                ts[blk["number"]] = int(t, 16) if isinstance(t, str) else t
            for log in batch.get("logs") or []:
                # default join only; keep exactly the contract and event we asked for
                if log["address"].lower() == EMITTER and log["topic0"] == SPEND:
                    out.append((log["block_number"], log["topic1"], log["topic2"], int(log["topic3"], 16),
                                word(log["data"], 3) / 1e6, word(log["data"], 4)))
        if r["next_block"] >= b:
            return out, ts
        body["from_block"] = r["next_block"]


head = call("/height")["height"]
back = (datetime.datetime.now(UTC).timestamp() - T0) / 86400 + 0.5  # a little extra, filtered by timestamp below
start = int(head - back * BLOCKS_PER_DAY)
step = (head - start) // THREADS + 1
ranges = [(start + i * step, min(head, start + (i + 1) * step)) for i in range(THREADS)]
with ThreadPoolExecutor(THREADS) as ex:
    parts = list(ex.map(pull, ranges))

block_ts, seen, rows = {}, set(), []
for logs, ts in parts:
    block_ts.update(ts)
    for p in logs:
        if p[2] not in seen:  # one Spend per payment id
            seen.add(p[2]); rows.append(p)
rows = [p for p in rows if T0 <= block_ts[p[0]] < T1]
day = lambda b: datetime.datetime.fromtimestamp(block_ts[b], UTC).strftime("%Y-%m-%d")
ndays = round((T1 - T0) / 86400)

print(f"ether.fi Cash on Optimism, {START:%d %b} to {END:%d %b %Y} UTC ({ndays} days)")
print("Spend events by issuer:", dict(collections.Counter(SPONSORS[p[3]] for p in rows)))
print("Spend events by mode:  ", dict(collections.Counter(MODES[p[5]] for p in rows)))

# Card payments only: the Reap and Rain card issuers (PIX is Brazil's Pix rail, CardOrder is ordering a card)
cards = [p for p in rows if SPONSORS[p[3]] in ("Reap", "Rain")]
amounts = sorted(p[4] for p in cards)
by_safe, days_by_safe = collections.defaultdict(list), collections.defaultdict(set)
for p in cards:
    by_safe[p[1]].append(p[4]); days_by_safe[p[1]].add(day(p[0]))
typical = sorted(statistics.median(v) for v in by_safe.values())
print(f"\nCard payments {len(cards):,}  USD ${sum(amounts):,.0f}  cardholders {len(by_safe):,}")
print(f"Median payment ${statistics.median(amounts):,.2f}  under $100 {100 * sum(a < 100 for a in amounts) / len(amounts):.1f}%")
print(f"Typical payment per cardholder (median of each cardholder's own median) ${statistics.median(typical):,.2f}")
print(f"Cardholders whose typical payment is under $20: {100 * sum(t < 20 for t in typical) / len(typical):.1f}%")
print(f"Cardholders who paid on all {ndays} days: {sum(len(d) == ndays for d in days_by_safe.values()):,}")

per_day, safes, usd = collections.Counter(), collections.defaultdict(set), collections.Counter()
for p in cards:
    d = day(p[0]); per_day[d] += 1; safes[d].add(p[1]); usd[d] += p[4]
print("\nday         payments  cardholders  usd")
for d in sorted(per_day):
    print(f"{d}  {per_day[d]:>8,}  {len(safes[d]):>11,}  ${usd[d]:>12,.0f}")
