"""ERC-20 approvals revoked on Ethereum over the last 30 days, split into real cleanups and resets.

A revoke is a wallet sending approve(spender, 0) straight to an ERC-20 token. A grant is the same call with an
amount above zero. A revoke is a reset, not a cleanup, when the same wallet grants the same spender on the same
token again within an hour (USDT, for one, makes you set an allowance to zero before changing it).
Reads every successful approve() transaction and its Approval event with Envio HyperSync.
Python 3 standard library only. Set ENVIO_API_TOKEN first.
"""
import bisect, collections, json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
CHAINS = {"Ethereum": 1}  # add more, e.g. "Base": 8453, if you have the time
RESET_WINDOW = 3600  # seconds
APPROVE = "0x095ea7b3"  # approve(address,uint256)
APPROVAL = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"  # Approval(address,address,uint256)
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
UNLIMITED = 2**255  # anything this big is an "infinite" approval (most wallets use 2**256-1)


def post(chain, body):
    req = urllib.request.Request(f"https://{chain}.hypersync.xyz/query", data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer " + TOKEN, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    for attempt in range(10):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("HyperSync request kept failing")


def block_at(chain, ts):
    """First block with timestamp >= ts, by binary search on HyperSync block headers (no block time assumed)."""
    def stamp(n):
        r = post(chain, {"from_block": n, "to_block": n + 1, "include_all_blocks": True,
                         "field_selection": {"block": ["number", "timestamp"]}})
        b = r["data"][0]["blocks"][0]
        return int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
    lo, hi = 0, post(chain, {"from_block": 0, "to_block": 1, "field_selection": {"block": ["number"]}})["archive_height"] - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if stamp(mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def scan_range(chain, start, end):
    txs, logs, stamps, fb = [], collections.defaultdict(list), {}, start
    while fb < end:
        r = post(chain, {"from_block": fb, "to_block": end, "join_mode": "JoinAll",
                         "transactions": [{"sighash": [APPROVE]}],
                         "field_selection": {"transaction": ["hash", "block_number", "from", "to", "input", "status"],
                                             "log": ["transaction_hash", "address", "topic0", "topic1", "topic2", "topic3", "data"],
                                             "block": ["number", "timestamp"]}})
        for d in r["data"]:
            txs += d.get("transactions") or []
            for l in d.get("logs") or []:
                logs[l["transaction_hash"]].append(l)
            for b in d.get("blocks") or []:
                stamps[b["number"]] = int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
        fb = r["next_block"]
    return txs, logs, stamps


def scan(chain, start, end, parts=30):
    """Every approve() transaction in [start, end) with its logs and block timestamps, fetched in parallel slices."""
    cuts = [start + (end - start) * i // parts for i in range(parts + 1)]
    txs, logs, stamps, done = [], collections.defaultdict(list), {}, 0
    with ThreadPoolExecutor(8) as pool:
        for t, l, s in pool.map(lambda i: scan_range(chain, cuts[i], cuts[i + 1]), range(parts)):
            txs += t
            logs.update(l)
            stamps.update(s)
            done += 1
            print(f"  ...{done}/{parts} slices", file=sys.stderr, flush=True)
    return txs, logs, stamps


def classify(txs, logs, stamps):
    """Keep successful approve() calls whose own ERC-20 Approval event (3 topics) matches the call."""
    out = []
    for t in txs:
        if t.get("status") != 1 or not t.get("to") or len(t["input"]) < 138:
            continue
        spender = "0x" + t["input"][34:74].lower()
        amount = int(t["input"][74:138], 16)
        ev = [l for l in logs[t["hash"]] if l.get("topic0") == APPROVAL and not l.get("topic3")
              and l["address"].lower() == t["to"].lower() and l.get("topic1") and l.get("topic2")
              and "0x" + l["topic1"][-40:] == t["from"].lower() and "0x" + l["topic2"][-40:] == spender]
        if not ev or int(ev[-1]["data"][:66], 16) != amount:
            continue  # not an ERC-20 approve (e.g. ERC-721 approve has the same selector), or a non-standard token
        day = datetime.fromtimestamp(stamps[t["block_number"]], timezone.utc).strftime("%Y-%m-%d")
        out.append({"day": day, "ts": stamps[t["block_number"]], "hash": t["hash"], "block": t["block_number"], "owner": t["from"].lower(),
                    "token": t["to"].lower(), "spender": spender, "amount": amount})
    return out


def main():
    days = int(os.environ.get("DAYS", "30"))
    end_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    if os.environ.get("END_DAY"):
        end_day = datetime.fromisoformat(os.environ["END_DAY"]).replace(tzinfo=timezone.utc)
    start_day = end_day - timedelta(days=days)
    print(f"Direct ERC-20 approve() calls, {start_day:%d %b} to {end_day - timedelta(days=1):%d %b %Y} UTC ({days} days)")
    result = {}
    only = os.environ.get("CHAIN")
    for name, chain in CHAINS.items():
        if only and only != name:
            continue
        t0 = time.time()
        a, b = block_at(chain, int(start_day.timestamp())), block_at(chain, int(end_day.timestamp()))
        txs, logs, stamps = scan(chain, a, b)
        rows = classify(txs, logs, stamps)
        secs = time.time() - t0
        rev = [r for r in rows if r["amount"] == 0]
        grant = [r for r in rows if r["amount"] > 0]
        unl = [r for r in grant if r["amount"] >= UNLIMITED]
        regrants = collections.defaultdict(list)
        for r in grant:
            regrants[(r["owner"], r["token"], r["spender"])].append(r["ts"])
        for v in regrants.values():
            v.sort()

        def is_reset(r):
            ts = regrants.get((r["owner"], r["token"], r["spender"]), [])
            i = bisect.bisect_left(ts, r["ts"])
            return i < len(ts) and ts[i] - r["ts"] <= RESET_WINDOW
        resets = [r for r in rev if is_reset(r)]
        clean = [r for r in rev if not is_reset(r)]
        daily = collections.defaultdict(lambda: [0, 0])
        for r in rows:
            daily[r["day"]][0 if r["amount"] == 0 else 1] += 1
        print(f"\n{name}  blocks {a:,} to {b - 1:,}  ({len(txs):,} approve() txs scanned in {secs:.0f}s)")
        print(f"  revokes  {len(rev):>9,}  by {len({r['owner'] for r in rev}):,} wallets on {len({r['token'] for r in rev}):,} tokens")
        print(f"  grants   {len(grant):>9,}  by {len({r['owner'] for r in grant}):,} wallets ({len(unl):,} unlimited)")
        print(f"    resets   {len(resets):>9,}  (re-approved within an hour, {sum(r['token'] == USDT for r in resets):,} of them USDT)")
        print(f"    cleanups {len(clean):>9,}  by {len({r['owner'] for r in clean}):,} wallets")
        top = collections.Counter(r["spender"] for r in clean).most_common(3)
        print("    most cleaned-up spenders  " + ", ".join(f"{s} ({n:,})" for s, n in top))
        print(f"  revokes per 100 grants  {100 * len(rev) / max(1, len(grant)):.1f}")
        cday = collections.Counter(r["day"] for r in clean)
        print("  day          revokes  cleanups    grants")
        for d in sorted(daily):
            print(f"  {d}  {daily[d][0]:>8,}  {cday[d]:>8,}  {daily[d][1]:>8,}")
        result[name] = {"from_block": a, "to_block": b - 1, "rows": rows, "daily": dict(daily), "cleanups": dict(cday)}
    if os.environ.get("DUMP"):
        json.dump(result, open(os.environ["DUMP"], "w"))


if __name__ == "__main__":
    main()
