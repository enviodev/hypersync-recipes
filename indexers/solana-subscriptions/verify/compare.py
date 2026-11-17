"""Compare RPC-decoded pulls into Helius's USDC account with the indexer's Pull rows."""
import json, sys
TREAS = "G2wv6MCDcaiqhbP4JqP6RB76utwAhhG4BoZ71r58zgk6"
rpc = [json.loads(l) for l in open(sys.argv[1])]
idx = {(p["txSignature"]): p for p in json.load(open(sys.argv[2])) if p["receiverAta"] == TREAS}
rp = {}
mism = 0; delta_mism = 0
for r in rpc:
    for i in r.get("ixs", []):
        if i.get("receiverAta") == TREAS:
            rp[r["sig"]] = i
            if i["receiverDelta"] != i["amount"]: delta_mism += 1
checked = set(r["sig"] for r in rpc)
idx_c = {s: p for s, p in idx.items() if s in checked}
for s, i in rp.items():
    p = idx_c.get(s)
    if not p or int(p["amount"]) != i["amount"]: mism += 1
print("rpc txs checked", len(checked), "rpc pulls to treasury", len(rp), "USDC", sum(i["amount"] for i in rp.values()) / 1e6)
print("indexer pulls in same txs", len(idx_c), "USDC", sum(int(p["amount"]) for p in idx_c.values()) / 1e6)
print("amount mismatches", mism, "| pulls where treasury balance change != instruction amount", delta_mism)
print("indexer-only", len(set(idx_c) - set(rp)), "rpc-only", len(set(rp) - set(idx_c)))
print("indexer Helius pulls total", len(idx), sum(int(p["amount"]) for p in idx.values()) / 1e6)
