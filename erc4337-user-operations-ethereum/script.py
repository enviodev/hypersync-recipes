"""Every ERC-4337 user operation on Ethereum, from the EntryPoint's UserOperationEvent.

Smart accounts on Ethereum send their transactions as user operations through an
EntryPoint contract. Each one emits a UserOperationEvent with the account that
sent it and the paymaster that paid its gas (the zero address if the account
paid for itself). This script reads that event from EntryPoint v0.6, v0.7 and
v0.8 with Envio HyperSync and prints user operations per day, the accounts
behind them, how many had their gas paid by a paymaster and how many of those
went through Pimlico's paymasters.

Usage:  ENVIO_API_TOKEN=... python3 script.py [START END]
        START and END are UTC dates (YYYY-MM-DD), both included.
        Default: the last 21 full UTC days.
"""
import collections, datetime, json, os, sys, time, urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN")
HS = "https://eth.hypersync.xyz"
# EntryPoint contracts, from https://docs.erc4337.io and github.com/eth-infinitism/account-abstraction
ENTRY_POINTS = {
    "0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789": "v0.6",
    "0x0000000071727de22e5e9d8baf0edac6f37da032": "v0.7",
    "0x4337084d9e255ff0702461cf8895ce9e3b5ff108": "v0.8",
}
# UserOperationEvent(bytes32 indexed userOpHash, address indexed sender, address indexed paymaster,
#                    uint256 nonce, bool success, uint256 actualGasCost, uint256 actualGasUsed)
USER_OP = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
# Pimlico's paymasters, from https://docs.pimlico.io/references/paymaster/erc20-paymaster/contract-addresses
PIMLICO = {
    "0x6666666666667849c56f2850848ce1c4da65c68b",  # for EntryPoint v0.6
    "0x777777777777aec03fd955926dbf81597e66834c",  # for EntryPoint v0.7
    "0x888888888888ec68a58ab8094cc1ad20ba3d2402",  # for EntryPoint v0.8
}
NO_PAYMASTER = "0x" + "0" * 40
UTC = datetime.timezone.utc
if len(sys.argv) == 3:
    START, END = (datetime.datetime.strptime(a, "%Y-%m-%d").replace(tzinfo=UTC) for a in sys.argv[1:3])
else:
    today = datetime.datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    START, END = today - datetime.timedelta(days=21), today - datetime.timedelta(days=1)
T0, T1 = START.timestamp(), (END + datetime.timedelta(days=1)).timestamp()
BLOCKS_PER_DAY = 7_200  # Ethereum makes a block every 12 seconds


def call(path, body=None):
    for attempt in range(30):
        try:
            req = urllib.request.Request(HS + path, json.dumps(body).encode() if body else None,
                                         {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json",
                                          "User-Agent": "envio-recipe"})
            res = json.load(urllib.request.urlopen(req, timeout=180))
            time.sleep(0.2)  # stay well inside the rate limit
            return res
        except Exception:
            time.sleep(min(30, 3 * (attempt + 1)))
    raise SystemExit("HyperSync request failed")


head = call("/height")["height"]
back = (datetime.datetime.now(UTC).timestamp() - T0) / 86400 + 0.5  # a little extra, filtered by timestamp below
body = {"from_block": int(head - back * BLOCKS_PER_DAY), "to_block": head,
        "logs": [{"address": list(ENTRY_POINTS), "topics": [[USER_OP]]}],
        "field_selection": {"log": ["address", "topic0", "topic2", "topic3", "block_number"],
                            "block": ["number", "timestamp"]}}
block_ts, rows = {}, []
while True:
    r = call("/query", body)
    for batch in r["data"]:
        for blk in batch.get("blocks") or []:
            t = blk["timestamp"]
            block_ts[blk["number"]] = int(t, 16) if isinstance(t, str) else t
        for log in batch.get("logs") or []:
            # default join only; keep exactly the contracts and event we asked for
            if log["address"].lower() in ENTRY_POINTS and log["topic0"] == USER_OP:
                rows.append((log["block_number"], ENTRY_POINTS[log["address"].lower()],
                             "0x" + log["topic2"][26:], "0x" + log["topic3"][26:]))
    if r["next_block"] >= head:
        break
    body["from_block"] = r["next_block"]

rows = [x for x in rows if T0 <= block_ts[x[0]] < T1]
day = lambda b: datetime.datetime.fromtimestamp(block_ts[b], UTC).strftime("%Y-%m-%d")
ndays = round((T1 - T0) / 86400)
n = len(rows)
paid = sum(x[3] != NO_PAYMASTER for x in rows)
pimlico = sum(x[3] in PIMLICO for x in rows)

print(f"ERC-4337 on Ethereum, {START:%d %b} to {END:%d %b %Y} UTC ({ndays} days)")
print(f"User operations {n:,}  ({n / ndays:,.0f} a day)  from {len({x[2] for x in rows}):,} accounts")
print("By EntryPoint:", dict(collections.Counter(x[1] for x in rows)))
print(f"Gas paid by a paymaster: {paid:,} ({100 * paid / n:.1f}%)")
print(f"Through Pimlico's paymasters: {pimlico:,} ({100 * pimlico / n:.1f}%)")

per_day = collections.defaultdict(lambda: [0, set(), 0, 0])
for b, _, sender, pm in rows:
    d = per_day[day(b)]
    d[0] += 1; d[1].add(sender); d[2] += pm != NO_PAYMASTER; d[3] += pm in PIMLICO
print("\nday         user ops  accounts  paymaster  pimlico")
for d in sorted(per_day):
    v = per_day[d]
    print(f"{d}  {v[0]:>8,}  {len(v[1]):>8,}  {v[2]:>9,}  {v[3]:>7,}")
