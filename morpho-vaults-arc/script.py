"""Morpho vaults on Arc, pulled with Envio HyperSync.

Reads every vault created by Morpho's VaultV2Factory on Arc, every deposit and
withdrawal in those vaults, and every borrow and repay on Morpho Blue on Arc.
Prints vault deposits, depositors, the biggest vaults, and what is borrowed
against cirBTC, then checks the vault totals against each vault's
totalAssets() over RPC.

    export ENVIO_API_TOKEN=your-token
    python script.py            # up to the latest block
    python script.py 30581168   # rerun the snapshot used in the post
"""
import collections, datetime as dt, json, os, sys, time, urllib.request

HYPERSYNC = "https://arc.hypersync.xyz"
RPC = "https://rpc.mainnet.arc.io"
TOKEN = os.environ["ENVIO_API_TOKEN"]

# Morpho on Arc, from https://docs.morpho.org/get-started/resources/addresses
MORPHO = "0x34cd04070dd72b14e241112f6d83812df5af7fcd"         # Morpho Blue
VAULT_FACTORY = "0x3b0eefabfa22ec7cf2c73877ac16e78d76749f12"  # VaultV2Factory
USDC = "0x3600000000000000000000000000000000000000"           # USDC on Arc, 6 decimals in its ERC-20 interface
CIRBTC = "0x171a4217b86a807a64eb94757db6849fb4bdbaa0"         # Circle Wrapped Bitcoin, 8 decimals

# event topic0s
CREATE_VAULT = "0x341ce009267aa0d78cc12b34155e223904a51ed49d144beb6eb8be87813edb4e"  # CreateVaultV2(owner, asset, salt, newVaultV2)
DEPOSIT = "0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7"       # Deposit(sender, onBehalf, assets, shares)
WITHDRAW = "0xfbde797d201c681b91056529119e0b02407c7bb96a4a2c75c01fc9667232c8db"      # Withdraw(sender, receiver, onBehalf, assets, shares)
CREATE_MARKET = "0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac"
BORROW = "0x570954540bed6b1304a87dfe815a5eda4a648f7097a16240dcd85c9b5fd42a43"        # Borrow(id, caller, onBehalf, receiver, assets, shares)
REPAY = "0x52acb05cebbd3cd39715469f22afbf5a17496295ef3bc9bb5944056c63ccaa09"         # Repay(id, caller, onBehalf, assets, shares)


def post(url, body, headers):
    # some public RPCs refuse Python's default user agent, so send a plain one
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"User-Agent": "hypersync-recipe", **headers})
    for attempt in range(8):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception as err:
            print("retrying:", err, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    sys.exit("request failed")


def logs(addresses, topics, to_block):
    """Every log from these addresses with one of these topic0s, up to to_block."""
    body = {
        "from_block": 0,
        "logs": [{"address": addresses, "topics": [topics]}],
        "field_selection": {
            "block": ["number", "timestamp"],
            "log": ["block_number", "log_index", "address", "topic0", "topic1", "topic2", "topic3", "data"],
        },
    }
    if to_block:
        body["to_block"] = to_block
    want_addr, want_topic = {a.lower() for a in addresses}, set(topics)
    out = []
    while True:
        res = post(HYPERSYNC + "/query", body, {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
        for batch in res["data"]:
            ts = {b["number"]: int(b["timestamp"], 16) for b in batch.get("blocks") or []}
            for log in batch.get("logs") or []:
                # keep only logs whose address and topic0 both match
                if log["address"].lower() in want_addr and log["topic0"] in want_topic:
                    log["ts"] = ts[log["block_number"]]
                    out.append(log)
        end = to_block or res["archive_height"]
        if res["next_block"] >= end:
            return out, end
        body["from_block"] = res["next_block"]


def eth_call(to, data, block):
    res = post(RPC, {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                     "params": [{"to": to, "data": data}, hex(block)]}, {"Content-Type": "application/json"})
    return res.get("result") or "0x"


def word(data, i):
    return int(data[2 + 64 * i: 66 + 64 * i], 16)


def addr(topic):
    return "0x" + topic[-40:]


def text(raw):
    try:
        n = int(raw[66:130], 16)
        return bytes.fromhex(raw[130:130 + 2 * n]).decode()
    except Exception:
        return "?"


def day(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d")


def main():
    to_block = int(sys.argv[1]) if len(sys.argv) > 1 else None

    created, height = logs([VAULT_FACTORY], [CREATE_VAULT], to_block)
    vault_asset = {addr(l["topic3"]): addr(l["topic2"]) for l in created}
    usdc_vaults = [v for v, a in vault_asset.items() if a == USDC]
    print(f"Morpho vaults on Arc, up to block {height:,}")
    print(f"  {len(vault_asset)} vaults created through VaultV2Factory, {len(usdc_vaults)} of them USDC vaults")

    flows, _ = logs(list(vault_asset), [DEPOSIT, WITHDRAW], height)
    net = collections.Counter()
    depositors = set()
    per_vault_depositors = collections.defaultdict(set)
    daily = collections.Counter()
    deposit_count = 0
    for l in flows:
        v = l["address"].lower()
        if vault_asset[v] != USDC:
            continue
        amount = word(l["data"], 0) / 1e6
        if l["topic0"] == DEPOSIT:
            owner = addr(l["topic2"])
            depositors.add(owner)
            per_vault_depositors[v].add(owner)
            net[v] += amount
            daily[day(l["ts"])] += amount
            deposit_count += 1
        else:
            net[v] -= amount
            daily[day(l["ts"])] -= amount
    print(f"  {deposit_count:,} USDC deposits from {len(depositors):,} wallets into {len(per_vault_depositors)} vaults")
    print(f"  USDC deposited, net of withdrawals: ${sum(net.values()):,.0f}")

    # second method: each vault's totalAssets() over RPC (includes interest earned)
    total_assets = {}
    for v in usdc_vaults:
        raw = eth_call(v, "0x01e1d114", height)
        total_assets[v] = int(raw, 16) / 1e6 if raw not in ("0x", "") else 0
    print(f"  USDC in the vaults now, from totalAssets() over RPC: ${sum(total_assets.values()):,.0f}")

    print("  biggest USDC vaults (RPC totalAssets, depositor wallets)")
    for v in sorted(usdc_vaults, key=lambda v: -total_assets[v])[:6]:
        name = text(eth_call(v, "0x06fdde03", height))
        print(f"    {name:<28} ${total_assets[v]:>14,.0f}  {len(per_vault_depositors[v]):>5} wallets  {v}")

    print("  USDC in the vaults at the end of each day (deposits minus withdrawals)")
    running = 0
    for d in sorted(daily):
        running += daily[d]
        if abs(daily[d]) >= 1_000_000:
            print(f"    {d}  {daily[d]:>+15,.0f}  ->  ${running:>14,.0f}")

    # what the vault USDC is lent against: Morpho Blue USDC/cirBTC markets
    events, _ = logs([MORPHO], [CREATE_MARKET, BORROW, REPAY], height)
    markets = {l["topic1"] for l in events if l["topic0"] == CREATE_MARKET
               and addr(l["data"][2:66]) == USDC and addr(l["data"][66:130]) == CIRBTC}
    principal = collections.Counter()
    borrowers = set()
    for l in events:
        if l["topic1"] not in markets:
            continue
        if l["topic0"] == BORROW:
            who = addr(l["topic2"])
            borrowers.add(who)
            principal[who] += word(l["data"], 1) / 1e6
        elif l["topic0"] == REPAY:
            principal[addr(l["topic3"])] -= word(l["data"], 0) / 1e6
    owed = 0
    supplied = 0
    for m in markets:
        raw = eth_call(MORPHO, "0x5c60e39a" + m[2:], height)
        supplied += word(raw, 0) / 1e6
        owed += word(raw, 2) / 1e6
    print("\nUSDC lent against cirBTC on Morpho on Arc")
    print(f"  {len(markets)} USDC/cirBTC markets, {len(borrowers):,} wallets have borrowed")
    print(f"  principal outstanding from events: ${sum(x for x in principal.values() if x > 0):,.0f}")
    print(f"  owed now, totalBorrowAssets over RPC: ${owed:,.0f} of ${supplied:,.0f} supplied ({owed / supplied:.0%} lent out)")


if __name__ == "__main__":
    main()
