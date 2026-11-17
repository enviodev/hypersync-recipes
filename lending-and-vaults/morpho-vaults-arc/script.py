"""Morpho vaults on Arc, pulled with Envio HyperSync.

Reads every vault created by Morpho's VaultV2Factory on Arc, every deposit,
withdrawal, interest accrual and adapter in those vaults, and every supply,
withdraw, borrow, repay, interest and liquidation event in the USDC/cirBTC
markets on Morpho Blue on Arc. Prints vault deposits, depositors, the biggest
vaults, and what is borrowed against cirBTC, all rebuilt from those events,
then checks them against totalAssets(), market() and position() over RPC.

    export ENVIO_API_TOKEN=your-token
    python script.py            # up to the latest block
    python script.py 30839502   # rerun the snapshot in the README
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
SUPPLY = "0xedf8870433c83823eb071d3df1caa8d008f12f6440918c20d75a3602cda30fe0"        # Supply(id, caller, onBehalf, assets, shares)
MARKET_WITHDRAW = "0xa56fc0ad5702ec05ce63666221f796fb62437c32db1aa1aa075fc6484cf58fbf"  # Withdraw(id, caller, onBehalf, receiver, assets, shares)
MARKET_ACCRUE = "0x9d9bd501d0657d7dfe415f779a620a62b78bc508ddc0891fbbd8b7ac0f8fce87"    # AccrueInterest(id, prevBorrowRate, interest, feeShares)
LIQUIDATE = "0xa4946ede45d0c6f06a0f5ce92c9ad3b4751452d2fe0e25010783bcab57a67e41"        # Liquidate(id, caller, borrower, repaid, repaidShares, seized, badDebt, badDebtShares)
VAULT_ACCRUE = "0x4dec04e750ca11537cabcd8a9eab06494de08da3735bc8871cd41250e190bc04"     # VaultV2 AccrueInterest(previousTotalAssets, newTotalAssets, perfFeeShares, mgmtFeeShares)
ADD_ADAPTER = "0x8f125a24838c4c23e893904b255b5c672d43d4cb8af7e3d15841eaeabc1e68aa"      # VaultV2 AddAdapter(account)


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

    flows, _ = logs(list(vault_asset), [DEPOSIT, WITHDRAW, VAULT_ACCRUE, ADD_ADAPTER], height)
    flows.sort(key=lambda l: (l["block_number"], int(l["log_index"], 16) if isinstance(l["log_index"], str) else l["log_index"]))
    # Each vault's stored totalAssets, rebuilt the way VaultV2 keeps it: set by AccrueInterest, then plus deposits
    # and minus withdrawals. Adapters are the contracts a vault lends through, from AddAdapter.
    total_assets = collections.Counter()
    adapter_vault = {}
    net = collections.Counter()
    depositors = set()
    per_vault_depositors = collections.defaultdict(set)
    daily = collections.Counter()
    deposit_count = 0
    for l in flows:
        v = l["address"].lower()
        if vault_asset[v] != USDC:
            continue
        if l["topic0"] == ADD_ADAPTER:
            adapter_vault[addr(l["topic1"])] = v
            continue
        if l["topic0"] == VAULT_ACCRUE:
            total_assets[v] = word(l["data"], 1) / 1e6
            continue
        amount = word(l["data"], 0) / 1e6
        total_assets[v] += amount if l["topic0"] == DEPOSIT else -amount
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

    print(f"  USDC in the vaults now, with interest (rebuilt totalAssets): ${sum(total_assets.values()):,.0f}")

    # cross-check: each vault's totalAssets() over RPC, which also adds interest accrued since the vault's last event
    rpc_assets = 0
    for v in usdc_vaults:
        raw = eth_call(v, "0x01e1d114", height)
        rpc_assets += int(raw, 16) / 1e6 if raw not in ("0x", "") else 0
    print(f"  Check (RPC totalAssets()): ${rpc_assets:,.0f}, gap ${sum(total_assets.values()) - rpc_assets:,.0f}")

    print("  biggest USDC vaults (rebuilt totalAssets, depositor wallets)")
    for v in sorted(usdc_vaults, key=lambda v: -total_assets[v])[:6]:
        name = text(eth_call(v, "0x06fdde03", height))
        print(f"    {name:<28} ${total_assets[v]:>14,.0f}  {len(per_vault_depositors[v]):>5} wallets  {v}")

    print("  USDC in the vaults at the end of each day (deposits minus withdrawals)")
    running = 0
    for d in sorted(daily):
        running += daily[d]
        if abs(daily[d]) >= 1_000_000:
            print(f"    {d}  {daily[d]:>+15,.0f}  ->  ${running:>14,.0f}")

    # what the vault USDC is lent against: Morpho Blue USDC/cirBTC markets, rebuilt from their events the way
    # Morpho keeps them (totalSupplyAssets, totalSupplyShares, totalBorrowAssets, and supply shares per address)
    events, _ = logs([MORPHO], [CREATE_MARKET, SUPPLY, MARKET_WITHDRAW, BORROW, REPAY, MARKET_ACCRUE, LIQUIDATE], height)
    events.sort(key=lambda l: (l["block_number"], int(l["log_index"], 16) if isinstance(l["log_index"], str) else l["log_index"]))
    markets = {l["topic1"] for l in events if l["topic0"] == CREATE_MARKET
               and addr(l["data"][2:66]) == USDC and addr(l["data"][66:130]) == CIRBTC}
    state = {m: collections.Counter() for m in markets}   # supply_assets, supply_shares, borrow_assets
    shares = collections.Counter()                        # (supplier, market) -> supply shares
    principal = collections.Counter()
    borrowers = set()
    for l in events:
        m = l["topic1"]
        if m not in markets or l["topic0"] == CREATE_MARKET:
            continue
        st, w = state[m], [word(l["data"], i) for i in range((len(l["data"]) - 2) // 64)]
        if l["topic0"] == SUPPLY:
            st["supply_assets"] += w[0]
            st["supply_shares"] += w[1]
            shares[addr(l["topic3"]), m] += w[1]
        elif l["topic0"] == MARKET_WITHDRAW:
            st["supply_assets"] -= w[1]
            st["supply_shares"] -= w[2]
            shares[addr(l["topic2"]), m] -= w[2]
        elif l["topic0"] == BORROW:
            st["borrow_assets"] += w[1]
            who = addr(l["topic2"])
            borrowers.add(who)
            principal[who] += w[1] / 1e6
        elif l["topic0"] == REPAY:
            st["borrow_assets"] -= w[0]
            principal[addr(l["topic3"])] -= w[0] / 1e6
        elif l["topic0"] == MARKET_ACCRUE:
            st["supply_assets"] += w[1]
            st["borrow_assets"] += w[1]
            st["supply_shares"] += w[2]   # fee shares, minted to the fee recipient
        elif l["topic0"] == LIQUIDATE:
            st["borrow_assets"] -= w[0] + w[3]
            st["supply_assets"] -= w[3]
    supplied = sum(st["supply_assets"] for st in state.values()) / 1e6
    owed = sum(st["borrow_assets"] for st in state.values()) / 1e6

    # how much of the vault USDC sits in the cirBTC markets: vaults supply to Morpho through adapters
    in_cirbtc = collections.Counter()
    for (who, m), n in shares.items():
        if who in adapter_vault and state[m]["supply_shares"]:
            in_cirbtc[adapter_vault[who]] += n * state[m]["supply_assets"] / state[m]["supply_shares"] / 1e6
    vault_total = sum(total_assets.values())
    print("\nUSDC lent against cirBTC on Morpho on Arc")
    print(f"  {len(markets)} USDC/cirBTC markets, {len(borrowers):,} wallets have borrowed")
    print(f"  principal outstanding from events: ${sum(x for x in principal.values() if x > 0):,.0f}")
    print(f"  owed now with interest: ${owed:,.0f} of ${supplied:,.0f} supplied ({owed / supplied:.0%} lent out)")
    print(f"  vault USDC supplied to the USDC/cirBTC markets: ${sum(in_cirbtc.values()):,.0f} "
          f"({sum(in_cirbtc.values()) / vault_total:.0%} of the ${vault_total:,.0f} in the vaults)")

    # cross-check against Morpho over RPC at the same block: market() for owed, and position() for every
    # supplier whose parentVault() is a USDC vault
    rpc_owed, rpc_in, market_state = 0, 0, {}
    for m in markets:
        raw = eth_call(MORPHO, "0x5c60e39a" + m[2:], height)
        market_state[m] = (word(raw, 0), word(raw, 1))
        rpc_owed += word(raw, 2) / 1e6
    for (who, m) in {k for k in shares}:
        parent = eth_call(who, "0x0fe36536", height)
        if len(parent) < 66 or addr(parent[:66]) not in total_assets:
            continue
        pos = eth_call(MORPHO, "0x93c52062" + m[2:] + who[2:].rjust(64, "0"), height)
        assets, total_shares = market_state[m]
        if total_shares:
            rpc_in += word(pos, 0) * assets / total_shares / 1e6
    print(f"  Check (RPC market() totalBorrowAssets): ${rpc_owed:,.0f}, gap ${owed - rpc_owed:,.2f}")
    print(f"  Check (RPC position() with parentVault()): ${rpc_in:,.0f}, gap ${sum(in_cirbtc.values()) - rpc_in:,.2f}")


if __name__ == "__main__":
    main()
