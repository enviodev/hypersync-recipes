"""Independent check: decode the program's instructions straight from Solana RPC getTransaction.

Usage: python3 rpc_check.py sigs.txt out.json
Reads one signature per line; for each successful tx, finds every instruction (top-level and inner)
for the Subscriptions program, records its discriminator, and for pulls the amount, mint and the
receiver token account's actual USDC balance change.
"""
import json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

RPC = "https://api.mainnet-beta.solana.com"
PROG = "De1egAFMkMWZSN5rYXRj9CAdheBamobVNubTsi9avR44"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

def b58d(s):
    n = 0
    for c in s: n = n * 58 + B58.index(c)
    b = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\0" * (len(s) - len(s.lstrip("1"))) + b

def b58e(b):
    n = int.from_bytes(b, "big"); out = ""
    while n: n, r = divmod(n, 58); out = B58[r] + out
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + out

def call(sig):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "getTransaction",
                       "params": [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0}]}).encode()
    for i in range(8):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(RPC, body, {"Content-Type": "application/json"}), timeout=60))
            if r.get("result"): return r["result"]
        except Exception: pass
        time.sleep(5 + i * 5)
    return None

def check(sig):
    tx = call(sig)
    if tx is None: return {"sig": sig, "error": "fetch"}
    m = tx["meta"]
    if m["err"] is not None: return {"sig": sig, "failed": True, "ixs": []}
    keys = tx["transaction"]["message"]["accountKeys"] + m.get("loadedAddresses", {}).get("writable", []) + m.get("loadedAddresses", {}).get("readonly", [])
    ixs = [(ix, False) for ix in tx["transaction"]["message"]["instructions"]]
    for inner in m.get("innerInstructions", []):
        ixs += [(ix, True) for ix in inner["instructions"]]
    pre = {b["accountIndex"]: int(b["uiTokenAmount"]["amount"]) for b in m.get("preTokenBalances", []) if b["mint"] == USDC}
    post = {b["accountIndex"]: int(b["uiTokenAmount"]["amount"]) for b in m.get("postTokenBalances", []) if b["mint"] == USDC}
    out = []
    for ix, inner in ixs:
        if keys[ix["programIdIndex"]] != PROG: continue
        d = b58d(ix["data"])
        if not d or d[0] > 18: continue  # self-CPI event payloads start 0xe4
        row = {"disc": d[0], "inner": inner}
        if d[0] in (4, 5, 10):
            row["amount"] = int.from_bytes(d[1:9], "little")
            row["mint"] = b58e(d[41:73])
            accs = ix["accounts"]
            recv_idx = accs[4] if d[0] == 10 else accs[3]
            row["receiverAta"] = keys[recv_idx]
            row["receiverDelta"] = post.get(recv_idx, 0) - pre.get(recv_idx, 0)
        out.append(row)
    return {"sig": sig, "slot": tx["slot"], "time": tx["blockTime"], "ixs": out}

if __name__ == "__main__":
    # Sequential and resumable: the public endpoint rate-limits getTransaction hard.
    sigs = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    cache = sys.argv[2] + ".jsonl"
    done = {}
    try:
        for l in open(cache):
            r = json.loads(l)
            if not r.get("error"): done[r["sig"]] = r
    except FileNotFoundError: pass
    with open(cache, "a") as f:
        for n, s in enumerate(sigs):
            if s in done: continue
            r = check(s); done[s] = r
            f.write(json.dumps(r) + "\n"); f.flush()
            if n % 50 == 0: print(n, len(sigs), flush=True)
            time.sleep(0.4)
    res = [done[s] for s in sigs]
    json.dump(res, open(sys.argv[2], "w"))
    print("checked", len(res), "fetch errors", sum(1 for r in res if r.get("error")))
