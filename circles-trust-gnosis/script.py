# Circles on Gnosis Chain: live trust links between humans, month by month, with Envio HyperSync.
# Reads every RegisterHuman and Trust event from the Circles v2 Hub (address from docs.aboutcircles.com),
# replays them to get the trust links that are live at the end of each month, and counts the ones
# between two registered humans. The 5,000 invitation bot accounts (BotCreated events from Circles'
# invitations-at-scale contract) are registered as humans in the Hub, so they are left out.
# Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import datetime
import json
import os
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HYPERSYNC = "https://gnosis.hypersync.xyz"
HUB = "0xc12c1e50abb450d6205ea2c3fa861b3b834d13e8"           # Circles v2 Hub
BOT_FARM = "0xd28b7c4f148b1f1e190840a1f7a796c5525d8902"      # emits BotCreated for invitation bots
REGISTER_HUMAN = "0xfea7c1e1973c8be64c654eb06dc19ffbfc2e924d57544b9da0c0a27d3f893d77"  # RegisterHuman(address,address)
TRUST = "0xe60c754dd8ab0b1b5fccba257d6ebcd7d09e360ab7dd7a6e58198ca1f57cdcec"           # Trust(address,address,uint256)
BOT_CREATED = "0xb8f1aefe219ba5e06d235c434fd818344a8a168abb8cb25b29da68e97f9e1e46"     # BotCreated(address)
START = 36_400_000  # just before the Hub was deployed in October 2024
STEP = 250_000

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def get(path, body=None):
    req = urllib.request.Request(HYPERSYNC + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
    for attempt in range(30):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception:
            time.sleep(min(60, 3 * (attempt + 1)))  # also covers HyperSync's per-minute rate limit
    sys.exit("HyperSync kept failing")


def logs(address, topics, first, last):
    """Every log from `address` with one of `topics` in [first, last), with its block timestamp."""
    body = {"from_block": first, "to_block": last, "logs": [{"address": [address], "topics": [topics]}],
            "field_selection": {"block": ["number", "timestamp"],
                                "log": ["address", "block_number", "log_index", "topic0", "topic1", "topic2", "data"]}}
    rows = []
    while True:
        res = get("/query", body)
        ts = {}
        for batch in res["data"]:
            for b in batch.get("blocks") or []:
                ts[b["number"]] = int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
        for batch in res["data"]:
            for l in batch.get("logs") or []:
                if l["address"].lower() == address and l["topic0"] in topics:  # filter again in code
                    rows.append((l["block_number"], l["log_index"], ts[l["block_number"]], l["topic0"],
                                 l["topic1"], l.get("topic2"), l.get("data")))
        if res["next_block"] >= last:
            return rows
        body["from_block"] = res["next_block"]


end = int(sys.argv[1]) if len(sys.argv) > 1 else get("/height")["height"]

# 1. Invitation bot accounts
bots = {r[4] for r in logs(BOT_FARM, [BOT_CREATED], START, end)}

# 2. Every RegisterHuman and Trust event from the Hub, read in parallel block ranges
events, lock = [], threading.Lock()


def scan(first):
    rows = logs(HUB, [REGISTER_HUMAN, TRUST], first, min(first + STEP, end))
    with lock:
        events.extend(rows)


with ThreadPoolExecutor(6) as pool:
    list(pool.map(scan, range(START, end, STEP)))
events.sort()

# 3. Replay them. A Trust event sets the link's expiry; removing trust sets the expiry to "now",
#    so a link is live at time t when its latest expiry is after t.
def month_ends(t0, t1):
    d = datetime.datetime.fromtimestamp(t0, datetime.timezone.utc).replace(day=1, hour=0, minute=0, second=0)
    while True:
        d = (d + datetime.timedelta(days=32)).replace(day=1)
        if d.timestamp() > t1:
            return
        yield int(d.timestamp())


now = events[-1][2]
humans, expiry, rows, i = set(), {}, [], 0
for t in list(month_ends(events[0][2], now)) + [now + 1]:
    while i < len(events) and events[i][2] < t:
        _, _, _, topic0, t1, t2, data = events[i]
        if topic0 == REGISTER_HUMAN:
            if t1 not in bots:
                humans.add(t1)
        else:
            expiry[(t1, t2)] = int(data, 16)
        i += 1
    live = sum(1 for (a, b), e in expiry.items() if e > t and a != b and a in humans and b in humans)
    rows.append((datetime.datetime.fromtimestamp(t - 1, datetime.timezone.utc).date(), len(humans), live))

print(f"Circles v2 on Gnosis Chain, blocks {START:,} to {end:,}")
print(f"{len(bots):,} invitation bot accounts left out\n")
print(f"{'as of':<12}{'humans':>10}{'live trust links':>20}")
for day, h, live in rows:
    print(f"{str(day):<12}{h:>10,}{live:>20,}")
month_end, year_before = rows[-2], rows[-14]  # last full month, and the same month a year earlier
print(f"\n{month_end[0]}: {month_end[2]:,} live trust links between {month_end[1]:,} humans, "
      f"{month_end[2] / year_before[2]:.2f}x the {year_before[2]:,} on {year_before[0]}")
