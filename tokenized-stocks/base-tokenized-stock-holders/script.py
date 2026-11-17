"""Who holds Coinbase's tokenized stocks on Base.

Reads every Transfer of every Coinbase tokenized stock on Base with Envio HyperSync,
rebuilds each address's balance, and counts how many different stocks each holder owns.
Optional: set BASE_RPC_URL to keep only wallets (no code, or EIP-7702 delegated) with eth_getCode.
"""
import collections, concurrent.futures as cf, json, os, sys, time, urllib.request

TOKEN = os.environ.get("ENVIO_API_TOKEN") or sys.exit("Set ENVIO_API_TOKEN")
HS = "https://base.hypersync.xyz"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40
START = 49_000_000  # before the first stock token transfer (August 2026)


def post(path, body=None):
    for attempt in range(15):
        try:
            req = urllib.request.Request(HS + path, json.dumps(body).encode() if body else None,
                                         {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(5 * (attempt + 1))  # back off on rate limits
    raise SystemExit("HyperSync request failed")


def stock_tokens():
    # Coinbase's Tokenized Stocks API, linked from docs.base.org (tokenized stocks on Base)
    out, page = [], None
    while True:
        url = "https://api.coinbase.com/v1/tokenized-stocks" + (f"?page_token={page}" if page else "")
        d = json.load(urllib.request.urlopen(url, timeout=60))
        out += d["tokens"]
        page = d.get("next_page_token")
        if not page:
            return {t["contract_address"].lower(): t["symbol"] for t in out}


def scan(rng, tokens):
    b0, b1 = rng
    bal, first = collections.defaultdict(int), {}
    body = {"from_block": b0, "to_block": b1,
            "logs": [{"address": list(tokens), "topics": [[TRANSFER]]}],
            "field_selection": {"block": ["number", "timestamp"],
                                "log": ["address", "topic0", "topic1", "topic2", "data", "block_number"]}}
    while True:
        d = post("/query", body)
        for part in d["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) if isinstance(b["timestamp"], str) else b["timestamp"]
                  for b in part.get("blocks") or []}
            for log in part.get("logs") or []:
                token = log["address"].lower()
                if token not in tokens or log["topic0"] != TRANSFER:
                    continue  # keep only the logs we asked for
                src, dst = "0x" + log["topic1"][-40:], "0x" + log["topic2"][-40:]
                value = int(log["data"], 16) if log["data"] not in ("0x", "") else 0
                if src != ZERO:
                    bal[(token, src)] -= value
                if dst != ZERO:
                    bal[(token, dst)] += value
                    if value and (dst not in first or ts[log["block_number"]] < first[dst]):
                        first[dst] = ts[log["block_number"]]
        if d["next_block"] >= b1:
            return bal, first
        body["from_block"] = d["next_block"]


def is_wallet(addr, rpc, block):
    req = urllib.request.Request(rpc, json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getCode",
                                                  "params": [addr, hex(block)]}).encode(),
                                 {"Content-Type": "application/json"})
    for attempt in range(6):
        try:
            code = json.load(urllib.request.urlopen(req, timeout=20))["result"]
            # no code = plain wallet; 0xef0100 = EIP-7702 delegated wallet. Everything else (pools, vaults,
            # routers, smart-account proxies) is left out, so the wallet count errs on the low side.
            return code == "0x" or code.startswith("0xef0100")
        except Exception:
            time.sleep(attempt + 1)
    return None


def main():
    tokens = stock_tokens()
    head = post("/height")["height"]
    step = (head - START) // 24
    ranges = [(START + i * step, head if i == 23 else START + (i + 1) * step) for i in range(24)]
    bal, first = collections.defaultdict(int), {}
    with cf.ThreadPoolExecutor(4) as ex:
        for b, f in ex.map(lambda r: scan(r, tokens), ranges):
            for k, v in b.items():
                bal[k] += v
            for a, t in f.items():
                first[a] = min(t, first.get(a, t))
    held = collections.defaultdict(set)
    for (token, holder), v in bal.items():
        if v > 0:
            held[holder].add(token)
    print(f"Coinbase tokenized stocks on Base, {len(tokens)} listed, up to block {head:,}")
    print(f"{len(first):,} addresses have ever held one, {len(held):,} hold one now")
    rpc = os.environ.get("BASE_RPC_URL")
    if rpc:
        with cf.ThreadPoolExecutor(12) as ex:
            kinds = dict(zip(held, ex.map(lambda a: is_wallet(a, rpc, head - 1), held)))
        held = {a: s for a, s in held.items() if kinds[a]}
        print(f"{len(held):,} of them are wallets (pools, vaults and other contracts removed)")
    dist = collections.Counter(min(len(s), 5) for s in held.values())
    print("Different stocks held:")
    for k in range(1, 6):
        print(f"  {str(k) + '+' if k == 5 else k:<3} {dist[k]:>7,}")
    multi = sum(dist[k] for k in range(2, 6))
    print(f"Hold two or more: {multi:,} ({multi / len(held):.1%})")


if __name__ == "__main__":
    main()
