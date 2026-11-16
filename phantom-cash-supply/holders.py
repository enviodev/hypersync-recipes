"""Count wallets holding Phantom CASH right now, over Solana RPC (getProgramAccounts).

Reads every Token-2022 account for the CASH mint, sums balances per owner, and checks the
total against getTokenSupply. The response is large (a few hundred MB), so use your own RPC
if the public one times out:  SOLANA_RPC=https://your-rpc python holders.py
"""
import base64, collections, json, os, urllib.request

RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
T22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
CASH = "CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH"


def rpc(method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    req = urllib.request.Request(RPC, json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["result"]


# token account layout: mint 0..32, owner 32..64, amount 64..72
accounts = rpc("getProgramAccounts", [T22, {"encoding": "base64", "dataSlice": {"offset": 32, "length": 40},
                                             "filters": [{"memcmp": {"offset": 0, "bytes": CASH}}]}])
owners = collections.Counter()
for a in accounts:
    raw = base64.b64decode(a["account"]["data"][0])
    amount = int.from_bytes(raw[32:40], "little")
    if amount:
        owners[raw[:32]] += amount
supply = int(rpc("getTokenSupply", [CASH])["value"]["amount"])
print(f"token accounts            {len(accounts):,}")
print(f"wallets with any CASH     {len(owners):,}")
print(f"wallets with >= $1        {sum(1 for v in owners.values() if v >= 1_000_000):,}")
print(f"wallets with >= $10       {sum(1 for v in owners.values() if v >= 10_000_000):,}")
print(f"sum of balances           ${sum(owners.values()) / 1e6:,.2f}")
print(f"getTokenSupply            ${supply / 1e6:,.2f}")
