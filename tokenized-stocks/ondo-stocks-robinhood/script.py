# Ondo tokenized stocks on Robinhood Chain: every Uniswap v4 swap in their first week, with Envio HyperSync.
# Prints swaps and wallets per token, and how many swaps paired an Ondo token with the Robinhood Stock Token
# of the same company. Python 3 standard library only. Set ENVIO_API_TOKEN first.
import calendar
import collections
import json
import os
import sys
import time
import urllib.request

URL = "https://robinhood.hypersync.xyz"
RPC = "https://rpc.mainnet.chain.robinhood.com"  # only used to read token symbols
# Uniswap v4 PoolManager, from https://developers.uniswap.org/docs/protocols/v4/deployments (Robinhood Chain, 4663)
POOL_MANAGER = "0x8366a39cc670b4001a1121b8f6a443a643e40951"
INITIALIZE = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
SWAP = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
# Ondo's Robinhood Chain tokens, from the token sheet linked at https://docs.ondo.finance/addresses
ONDO = {
    "0x9bf86418caf2b7a939603d6c24219a77bf7f9b33": "AAPLon",
    "0x900f8970d2fae8060d06bb29234f629c837c3383": "BMNRon",
    "0x369c4748e98c153e9b7adebc3e71e9e2a5f60dc0": "CRCLon",
    "0x75113389169b154ddac67ca7efa542680d75f072": "FXIon",
    "0xb094d0d3221d7f7a9f14b0f78c34cd38d7acf6f2": "GMEon",
    "0xe10cc5f0cd0c90322ebeb33e7757b2c9090146dc": "GOOGLon",
    "0x43cac729218c62210d71d66b7f0ec93990d8d8cc": "HOODon",
    "0x7b5026cfcb4de0cf3d9a39fe2a541514b71437a2": "METAon",
    "0x09dedc334fc47ab543e5d70c7fd9d2b1aea175bd": "MSTRon",
    "0xf1b95ae4e7700b962714702ea53784dc8492a856": "NVDAon",
    "0x300fe8a40701ce81460503fb886f9ed81a3b5e14": "QQQon",
    "0x533c5571ae586985e1fddfaa24304284d970c62a": "SPYon",
    "0xb197f36c25ba9b66960688882a4dc595c6b04309": "TSLAon",
    "0xa8f72952653864f7457e0c307fdb415e03c2ece1": "CPERon",
    "0x9b8294f24453379aa87c807ab82bf1d5722153fc": "SPCXon",
}
TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")
# Launch week, 27th Oct to 3rd Nov 2026 UTC. Pass another start date (YYYY-MM-DD) to look at a different week.
start_day = sys.argv[1] if len(sys.argv) > 1 else "2026-10-27"
START = calendar.timegm(time.strptime(start_day, "%Y-%m-%d"))
END = START + 7 * 86400


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    for attempt in range(10):
        try:
            return json.load(urllib.request.urlopen(req, timeout=120))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def hypersync(body):
    return post(URL + "/query", body, {"Authorization": "Bearer " + TOKEN})


def symbol(address):
    out = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                     "params": [{"to": address, "data": "0x95d89b41"}, "latest"]}, {"User-Agent": "curl/8"})["result"][2:]
    if len(out) < 128:  # native ETH or a token without a string symbol
        return ""
    length = int(out[64:128], 16)
    return bytes.fromhex(out[128:128 + 2 * length]).decode(errors="replace")


def logs(topics, fields_tx=False):
    body = {"from_block": 0, "logs": [{"address": [POOL_MANAGER], "topics": topics}],
            "field_selection": {"block": ["number", "timestamp"],
                                "log": ["block_number", "address", "topic0", "topic1", "topic2", "topic3", "data",
                                        "transaction_hash"]}}
    if fields_tx:
        body["field_selection"]["transaction"] = ["hash", "from"]
    while True:
        res = hypersync(body)
        for batch in res["data"]:
            ts = {b["number"]: (int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"])
                  for b in batch.get("blocks") or []}
            sender = {t["hash"]: t["from"].lower() for t in batch.get("transactions") or []}
            for log in batch.get("logs") or []:
                if log["address"].lower() == POOL_MANAGER and log["topic0"].lower() == topics[0][0]:
                    yield log, ts.get(log["block_number"]), sender.get(log["transaction_hash"])
        if res["next_block"] >= res["archive_height"]:
            return
        body["from_block"] = res["next_block"]


# 1. Every Uniswap v4 pool with an Ondo token on either side.
padded = ["0x" + "0" * 24 + a[2:] for a in ONDO]
pools = {}
for topics in ([[INITIALIZE], [], padded], [[INITIALIZE], [], [], padded]):
    for log, _, _ in logs(topics):
        c0, c1 = "0x" + log["topic2"][-40:], "0x" + log["topic3"][-40:]
        ondo = c0 if c0 in ONDO else c1
        other = c1 if ondo == c0 else c0
        pools[log["topic1"].lower()] = (ONDO[ondo], other)
others = {o: symbol(o) for _, o in pools.values()}

# 2. Every swap in those pools during the week, with the wallet that sent it.
swaps = []
for log, ts, sender in logs([[SWAP], list(pools)], fields_tx=True):
    pid = log["topic1"].lower()
    if pid in pools and ts is not None and START <= ts < END:
        sym, other = pools[pid]
        same_stock = others[other] == sym[:-2]  # e.g. GOOGLon paired with GOOGL
        swaps.append((sym, sender, same_stock))

print(f"Ondo stocks on Robinhood Chain, {start_day} to 7 days later (UTC)")
print(f"Uniswap v4 pools with an Ondo token  {len(pools)}")
print(f"Swaps    {len(swaps)}")
print(f"Wallets  {len({s[1] for s in swaps})}")
paired = [s for s in swaps if s[2]]
print(f"Swaps against the same company's Robinhood Stock Token  {len(paired)} ({len(paired) / max(1, len(swaps)):.0%})")
per = collections.defaultdict(list)
for sym, sender, _ in swaps:
    per[sym].append(sender)
for sym, senders in sorted(per.items(), key=lambda kv: -len(kv[1])):
    print(f"  {sym:8} {len(senders):4} swaps from {len(set(senders)):3} wallets")
