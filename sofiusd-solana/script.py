# Every SoFiUSD mint and burn on Solana, with Envio HyperSync.
# Reads Token-2022 MintTo / MintToChecked / Burn / BurnChecked instructions on the SoFiUSD mint,
# rebuilds the supply over time, and prints it by month.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

HYPERSYNC = "https://solana.hypersync.xyz"
TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
SOFIUSD = "APhcqtzE73es3KAGiVksZFMLGwJDiAey5qZKUrQHEHfS"  # SoFiUSD (SOFID) on Solana, 6 decimals
START_SLOT = 370_000_000  # before SoFiUSD launched on Solana (first mint April 2026)

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def query(body):
    req = urllib.request.Request(HYPERSYNC + "/query", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    for attempt in range(40):
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e:
            # HyperSync says how long until the rate-limit window resets
            time.sleep(int(e.headers.get("x-ratelimit-reset") or 3) if e.code == 429 else 3)
        except Exception:
            time.sleep(3)
    sys.exit("HyperSync request kept failing")


# MintTo (7) and MintToChecked (14) take the mint as account 0. Burn (8) and BurnChecked (15) take it as account 1.
SELECTION = [
    {"executing_account": [TOKEN_2022], "d1": ["07", "0e"], "a0": [SOFIUSD]},
    {"executing_account": [TOKEN_2022], "d1": ["08", "0f"], "a1": [SOFIUSD]},
]

head = json.load(urllib.request.urlopen(HYPERSYNC + "/height"))
events, block_time = [], {}
start = START_SLOT
while start < head:
    end = min(start + (200_000 if head - start < 10_000_000 else 2_000_000), head)
    body = {"from_slot": start, "to_slot": end, "instruction_calls": SELECTION,
            "field_selection": {"instruction_call": ["slot", "data", "a0", "a1"], "block": ["slot", "block_time"]}}
    while body["from_slot"] < end:
        res = query(body)
        for batch in res.get("blocks") or []:
            for b in batch:
                if b.get("block_time"):
                    block_time[b["slot"]] = b["block_time"]
        for batch in res.get("instruction_calls") or []:
            for ix in batch:
                op = ix["data"][:2]
                # keep only rows whose instruction and mint position match, then read the u64 amount after the 1-byte tag
                if op in ("07", "0e") and ix["a0"] == SOFIUSD:
                    sign = 1
                elif op in ("08", "0f") and ix["a1"] == SOFIUSD:
                    sign = -1
                else:
                    continue
                amount = int.from_bytes(bytes.fromhex(ix["data"][2:18]), "little") / 1e6
                events.append((ix["slot"], sign * amount))
        if res["next_slot"] <= body["from_slot"]:
            break
        body["from_slot"] = res["next_slot"]
    start = end
    print(f"  read to slot {start:,} ({len(events)} mints and burns)", file=sys.stderr)

events.sort()
supply, months = 0.0, defaultdict(lambda: [0.0, 0.0, 0.0])
for slot, amount in events:
    supply += amount
    month = datetime.datetime.fromtimestamp(block_time[slot], datetime.UTC).strftime("%Y-%m")
    months[month][0 if amount > 0 else 1] += abs(amount)
    months[month][2] = supply

print(f"\n{'Month':8} {'Minted':>12} {'Burned':>12} {'Supply at end':>15}")
for month in sorted(months):
    minted, burned, end_supply = months[month]
    print(f"{month:8} {minted / 1e6:11.1f}M {burned / 1e6:11.1f}M {end_supply / 1e6:14.1f}M")
print(f"\nSoFiUSD supply on Solana from mints and burns: {supply:,.2f}")
print("Compare with Solana RPC getTokenSupply for", SOFIUSD)
