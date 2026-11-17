"""Independent checks on script.py's counts. Run script.py with DUMP=dump.json first, then: python check.py dump.json

1. Log-side recount: for three sample days per chain, start from Approval events instead of transactions, join each event
   to its transaction (sighash, from, to, status) and recount revokes and grants. Should match script.py day for day.
2. Public RPC spot check: 20 random revokes and 20 random grants per chain, fetched with eth_getTransactionByHash and
   eth_getTransactionReceipt from a public node. Each must be a successful approve() to the token with the same
   spender and amount, and its receipt must hold the matching Approval event.
3. Public RPC reset check: 20 random resets, with the revoke and its re-approval both fetched from a public node and
   their block timestamps compared.
"""
import collections, json, random, sys, urllib.request
from datetime import datetime, timezone
from script import post, APPROVAL, APPROVE

RPC = {"Ethereum": ["https://ethereum-rpc.publicnode.com", "https://eth.drpc.org", "https://1rpc.io/eth"]}
CHAINS = {"Ethereum": 1}


def rpc(urls, method, params):
    for url in urls:
        try:
            out = rpc_one(url, method, params)
            if out is not None:
                return out
        except Exception:
            pass
    raise RuntimeError(f"no public RPC returned {method} {params}")


def rpc_one(url, method, params):
    req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())["result"]


def day_blocks(rows, day):
    bs = [r["block"] for r in rows if r["day"] == day]
    return min(bs), max(bs) + 1


def logside(chain, start, end, day):
    seen, fb = {}, start
    while fb < end:
        r = post(chain, {"from_block": fb, "to_block": end, "logs": [{"topics": [[APPROVAL]]}],
                         "field_selection": {"log": ["transaction_hash", "address", "topic1", "topic3", "data", "block_number"],
                                             "transaction": ["hash", "from", "to", "status", "sighash"],
                                             "block": ["number", "timestamp"]}})
        for d in r["data"]:
            tx = {t["hash"]: t for t in d.get("transactions") or []}
            ts = {b["number"]: b["timestamp"] for b in d.get("blocks") or []}
            for l in d.get("logs") or []:
                t = tx.get(l["transaction_hash"])
                if l.get("topic3") or not l.get("topic1") or not t or t.get("sighash") != APPROVE or t.get("status") != 1:
                    continue
                if l["address"].lower() != (t.get("to") or "").lower() or "0x" + l["topic1"][-40:] != t["from"].lower():
                    continue
                stamp = ts.get(l["block_number"])
                stamp = int(stamp, 16) if isinstance(stamp, str) else stamp
                if stamp is not None and datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%d") != day:
                    continue
                seen[t["hash"]] = int(l["data"][:66], 16)
        fb = r["next_block"]
    v = list(seen.values())
    return sum(1 for a in v if a == 0), sum(1 for a in v if a > 0)


def spot(name, rows, n=20):
    url, ok = RPC[name], 0
    random.seed(7)
    picks = random.sample([r for r in rows if r["amount"] == 0], n) + random.sample([r for r in rows if r["amount"] > 0], n)
    for r in picks:
        tx = rpc(url, "eth_getTransactionByHash", [r["hash"]])
        rc = rpc(url, "eth_getTransactionReceipt", [r["hash"]])
        inp = tx["input"]
        good = (rc["status"] == "0x1" and tx["to"].lower() == r["token"] and tx["from"].lower() == r["owner"]
                and inp[:10] == APPROVE and "0x" + inp[34:74] == r["spender"] and int(inp[74:138], 16) == r["amount"]
                and int(tx["blockNumber"], 16) == r["block"]
                and any(l["topics"][0] == APPROVAL and len(l["topics"]) == 3 and l["address"].lower() == r["token"]
                        and int(l["data"][:66], 16) == r["amount"] for l in rc["logs"]))
        ok += good
        if not good:
            print("   MISMATCH", r["hash"])
    return ok, len(picks)


def resets(name, rows, n=20):
    """20 random resets: confirm on public RPC that the re-approval exists and landed within the hour."""
    url, ok = RPC[name], 0
    grants = collections.defaultdict(list)
    for r in rows:
        if r["amount"] > 0:
            grants[(r["owner"], r["token"], r["spender"])].append(r)
    pairs = []
    for r in rows:
        if r["amount"] == 0:
            later = [g for g in grants.get((r["owner"], r["token"], r["spender"]), []) if 0 <= g["ts"] - r["ts"] <= 3600]
            if later:
                pairs.append((r, min(later, key=lambda g: g["ts"])))
    random.seed(11)
    for rv, gr in random.sample(pairs, n):
        stamps = []
        for r in (rv, gr):
            tx = rpc(url, "eth_getTransactionByHash", [r["hash"]])
            rc = rpc(url, "eth_getTransactionReceipt", [r["hash"]])
            blk = rpc(url, "eth_getBlockByNumber", [tx["blockNumber"], False])
            good = rc["status"] == "0x1" and int(tx["input"][74:138], 16) == r["amount"] and "0x" + tx["input"][34:74] == r["spender"]
            stamps.append((good, int(blk["timestamp"], 16)))
        if stamps[0][0] and stamps[1][0] and 0 <= stamps[1][1] - stamps[0][1] <= 3600:
            ok += 1
        else:
            print("   MISMATCH", rv["hash"], gr["hash"])
    return ok, n


def main():
    dump = json.load(open(sys.argv[1]))
    for name, d in dump.items():
        rows, days = d["rows"], sorted(d["daily"])
        print(f"{name}")
        for day in (days[0], days[len(days) // 2], days[-1]):
            a, b = day_blocks(rows, day)
            rev, gr = logside(CHAINS[name], a, b, day)
            s = d["daily"][day]
            print(f"  log-side recount {day}: revokes {rev:,} vs {s[0]:,}, grants {gr:,} vs {s[1]:,}")
        ok, tot = spot(name, rows)
        print(f"  public RPC spot check: {ok}/{tot} transactions match")
        ok, tot = resets(name, rows)
        print(f"  public RPC reset check: {ok}/{tot} resets have their re-approval within the hour")


if __name__ == "__main__":
    main()
