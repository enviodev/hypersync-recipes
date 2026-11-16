# What people borrow against on Jupiter Lend, with Envio HyperSync.
# Pulls every init_position instruction on Jupiter Lend's vaults program on Solana (one per borrow position opened),
# groups the positions by the vault's collateral token, and checks each vault's count against Jupiter's own API.
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
# Program ID from https://developers.jup.ag/docs/lend/program-addresses, discriminator from the IDL at
# https://github.com/jup-ag/jupiter-lend/blob/main/target/idl/vaults.json
VAULTS_PROGRAM = "jupr81YtYssSyPt8jbnGuiWon5f6x9TcDEFxYe3Bdzi"
INIT_POSITION = "c5140a0161a0b15b"  # data: u16 vault_id, u32 next_position_id. Account 0 is the wallet
VAULTS_API = "https://lite-api.jup.ag/lend/v1/borrow/vaults"  # vault id -> collateral and debt token, total positions
STOCKS = {"SPYx", "QQQx", "NVDAx", "TSLAx"}  # the tokenized stocks and ETFs Jupiter Lend takes as collateral
FIRST_SLOT = 391_001_451  # 3 Jan 2026, the start of HyperSync's Solana history
SEGMENT = 1_000_000
WORKERS = 16

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "hypersync-recipe"}), timeout=60))


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
head = int(sys.argv[2]) if len(sys.argv) > 2 else get(HYPERSYNC + "/height")
lock = threading.Lock()
positions = {}  # (vault id, position id) -> (slot, block time, wallet)


def pull(segment):
    a, b = segment
    body = {
        "from_slot": a, "to_slot": b,
        "instruction_calls": [{"executing_account": [VAULTS_PROGRAM], "d8": [INIT_POSITION], "tx_success": True}],
        "field_selection": {"instruction_call": ["slot", "data", "a0"], "block": ["slot", "block_time"]},
    }
    while True:
        res = post(body)
        times = {blk["slot"]: blk["block_time"] for batch in res.get("blocks") or [] for blk in batch}
        with lock:
            for batch in res.get("instruction_calls") or []:
                for r in batch:
                    vault_id, position_id = struct.unpack_from("<HI", bytes.fromhex(r["data"]), 8)
                    positions[(vault_id, position_id)] = (r["slot"], times[r["slot"]], r["a0"])
        if res["next_slot"] >= b or res["next_slot"] <= body["from_slot"]:
            return
        body["from_slot"] = res["next_slot"]


segments = [(a, min(a + SEGMENT, head)) for a in range(start, head, SEGMENT)]
with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
    for i, _ in enumerate(pool.map(pull, segments), 1):
        print(f"  segment {i} of {len(segments)}", file=sys.stderr)

vaults = {v["id"]: v for v in get(VAULTS_API)}
collateral = lambda vault_id: vaults[vault_id]["supplyToken"]["symbol"] if vault_id in vaults else "not listed"
stock_slots = [slot for (vault_id, _), (slot, _, _) in positions.items() if collateral(vault_id) in STOCKS]
since = min(stock_slots)  # the first position opened against a stock token
since_time = min(t for (slot, t, _) in positions.values() if slot == since)
window = {k: v for k, v in positions.items() if v[0] >= since}

by_token, wallets = collections.Counter(), collections.defaultdict(set)
for (vault_id, _), (_, _, wallet) in window.items():
    by_token[collateral(vault_id)] += 1
    wallets[collateral(vault_id)].add(wallet)
stock_positions = sum(n for s, n in by_token.items() if s in STOCKS)
stock_wallets = set().union(*[wallets[s] for s in STOCKS])

when = datetime.datetime.fromtimestamp(since_time, datetime.timezone.utc).strftime("%d %b %Y")
print(f"Borrow positions opened on Jupiter Lend since the first stock-backed one (slot {since:,}, {when}), by collateral")
print(f"{'collateral':12} {'positions':>10} {'wallets':>9}")
for symbol, n in by_token.most_common(12):
    print(f"{symbol:12} {n:10,} {len(wallets[symbol]):9,}{'   stock' if symbol in STOCKS else ''}")
print(f"\nSlots {start:,} to {head:,}")
print(f"Positions opened in the whole window: {len(positions):,}")
print(f"Positions opened since slot {since:,}: {len(window):,}")
print(f"Backed by tokenized stocks: {stock_positions:,} ({100 * stock_positions / len(window):.1f}%), from {len(stock_wallets):,} wallets")

# Check: position ids count up from 1 in each vault, so the highest id we saw should equal the vault's
# totalPositions in Jupiter's API (or sit just under it if a position was opened after our last slot).
highest = collections.Counter()
for (vault_id, position_id) in positions:
    highest[vault_id] = max(highest[vault_id], position_id)
listed = [v for v in highest if v in vaults]
exact = sum(1 for v in listed if highest[v] == vaults[v]["totalPositions"])
behind = sum(1 for v in listed if 0 < vaults[v]["totalPositions"] - highest[v] <= 25)
print(f"Vaults whose highest position id equals Jupiter's totalPositions: {exact} of {len(listed)} ({behind} more are a few positions behind the live API)")
