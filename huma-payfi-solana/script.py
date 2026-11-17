"""Every Huma Institutional drawdown and principal repayment on Solana, by month.

Pulls every instruction executed by the Huma Institutional program with HyperSync,
decodes drawdown and make_principal_payment by their Anchor discriminators, and sums
the u128 `amount` argument (USDC, 6 decimals). Failed transactions are skipped.

Usage: ENVIO_API_TOKEN=... python3 script.py [from_slot] [to_slot]
"""
import collections, json, os, sys, time, urllib.request

PROGRAM = "EVQ4s1b6N1vmWFDv8PRNc77kufBP8HcrSNWXQAhRsJq9"  # Huma Institutional (docs.huma.finance)
DISC = {"c828a26f9cde07f3": "drawdown", "28494b8a2d608742": "make_principal_payment"}
URL = "https://solana.hypersync.xyz/query"
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")

def post(body):
    for i in range(8):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(),
                {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception as e:
            print("retry", e, file=sys.stderr); time.sleep(3 * (i + 1))
    raise SystemExit("query failed")

def head_slot():
    req = urllib.request.Request("https://api.mainnet-beta.solana.com",
        b'{"jsonrpc":"2.0","id":1,"method":"getSlot"}', {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))["result"]

FROM = int(sys.argv[1]) if len(sys.argv) > 1 else 391_001_451  # start of HyperSync's Solana archive
TO = int(sys.argv[2]) if len(sys.argv) > 2 else head_slot()

body = {"from_slot": FROM, "to_slot": TO,
        "instruction_calls": [{"executing_account": [PROGRAM]}],
        "field_selection": {"instruction_call": ["slot", "transaction_index", "instruction_address",
                                                  "executing_account", "data", "tx_success"],
                            "block": ["slot", "block_time"]}}
rows, times, seen = [], {}, set()
while True:
    r = post(body)
    for b in r.get("blocks") or []:
        for x in b: times[x["slot"]] = x.get("block_time")
    for b in r.get("instruction_calls") or []: rows += b
    if r["next_slot"] <= body["from_slot"] or r["next_slot"] >= TO: break
    body["from_slot"] = r["next_slot"]
    print("slot", r["next_slot"], "rows", len(rows), file=sys.stderr)

count = collections.defaultdict(collections.Counter)
usdc = collections.defaultdict(lambda: collections.defaultdict(int))
for x in rows:
    key = (x["slot"], x["transaction_index"], tuple(x.get("instruction_address") or []))
    if key in seen or x.get("tx_success") is False or x["executing_account"] != PROGRAM: continue
    seen.add(key)
    data = bytes.fromhex(x["data"][2:] if x["data"].startswith("0x") else x["data"])
    name = DISC.get(data[:8].hex())
    if not name: continue
    month = time.strftime("%Y-%m", time.gmtime(times[x["slot"]]))
    count[name][month] += 1
    usdc[name][month] += int.from_bytes(data[8:24], "little")

print(f"Slots {FROM:,} to {TO:,}")
for name in DISC.values():
    print(f"\n{name}")
    for m in sorted(count[name]):
        print(f"  {m}  {count[name][m]:4d}  ${usdc[name][m] / 1e6:,.2f}")
    print(f"  total {sum(count[name].values()):4d}  ${sum(usdc[name].values()) / 1e6:,.2f}")
