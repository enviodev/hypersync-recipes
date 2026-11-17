# Where tokenized Circle (CRCL) stock lives onchain, with Envio HyperSync.
# Finds every issuer's CRCL token from the issuers' own lists, replays every Transfer on the EVM chains HyperSync covers,
# and splits each token's supply into DEX pools, lending markets, other contracts and wallets.
# Solana and X Layer supply are read from their public RPCs. Python 3 standard library only. Set ENVIO_API_TOKEN first.
import collections
import csv
import io
import json
import os
import re
import sys
import time
import urllib.request

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40
CHAINS = {  # name: (HyperSync subdomain, public RPC)
    "Ethereum": ("eth", "https://ethereum-rpc.publicnode.com"),
    "BNB Chain": ("bsc", "https://bsc-dataseed.bnbchain.org"),
    "Robinhood": ("robinhood", "https://rpc.mainnet.chain.robinhood.com"),
    "Base": ("base", "https://mainnet.base.org"),
    "Ink": ("ink", "https://rpc-gel.inkonchain.com"),
    "Arbitrum": ("arbitrum", "https://arb1.arbitrum.io/rpc"),
    "Optimism": ("optimism", "https://mainnet.optimism.io"),
    "Mantle": ("mantle", "https://rpc.mantle.xyz"),
    "Monad": ("monad", "https://rpc.monad.xyz"),
    "HyperEVM": ("hyperliquid", "https://rpc.hyperliquid.xyz/evm"),
}
XLAYER_RPC = "https://rpc.xlayer.tech"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
# Issuer lists
ONDO_SHEET = ("https://www.dropbox.com/scl/fi/qjfxyg748mx0dwi6up86d/EXTERNAL-Ondo-GM-Tokens-Ondo-GM-Tokens.csv"
              "?rlkey=n3no1w78wrah3umsl0nr9s77i&dl=1")  # linked from docs.ondo.finance/addresses
XSTOCKS = "https://xstocks.fi/us/products"
ROBINHOOD = "https://api.robinhood.com/rhj/assets"  # docs.robinhood.com/chain/stock-tokens
COINBASE = "https://api.coinbase.com/v1/tokenized-stocks"  # docs.base.org/sdks/tokenized-stocks
# Binance's bStocks (bstocks.finance) are listed in Trust Wallet's token registry, which links back to bstocks.finance
BSTOCKS = ("https://raw.githubusercontent.com/trustwallet/assets/master/blockchains/smartchain/assets/"
           "0x80f3D493EBCe97e343c53D29a137942416B4ffC0/info.json")
# xStocks mints every EVM token to this wallet and sends it out from there, so its balance is not yet issued to anyone.
XSTOCKS_MINT_WALLET = "0x5f7a4c11bde4f218f0025ef444c369d838ffa2ad"
XSTOCKS_SOLANA_MINTER = "S7vYFFWH6BjJyEsdrPQpqpYTqLTrPRK6KW3VwsJuRaS"  # the mint's creator, labelled xStocks Minter on Solscan
BINANCE_HOT_WALLET_20 = "0xf977814e90da44bfa03b6295a0616a897441acec"  # labelled "Binance: Hot Wallet 20" on BscScan
# Lending and DEX singletons that hold tokens for many markets or pools
SINGLETONS = {
    "0x8f73b65b4caaf64fba2af91cc5d4a2a1318e5d8c": "lending",  # Lista DAO Moolah (BNB Chain)
    "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb": "lending",  # Morpho (Ethereum, Base)
    "0x000000000004444c5dc75cb358380d2e3de08a90": "dex",      # Uniswap v4 PoolManager (Ethereum)
    "0x28e2ea090877bf75740558f6bfb36a5ffee9e9df": "dex",      # Uniswap v4 PoolManager (BNB Chain)
    "0x8366a39cc670b4001a1121b8f6a443a643e40951": "dex",      # Uniswap v4 PoolManager (Robinhood)
    "0x498581ff718922c3f8e6a244956af099b2652b2b": "dex",      # Uniswap v4 PoolManager (Base)
    "0x360e68faccca8ca495c1b759fd9eee466db9fb32": "dex",      # Uniswap v4 PoolManager (Arbitrum, Ink)
    "0x9a13f98cb987694c9f086b1f5eb990eea8264ec3": "dex",      # Uniswap v4 PoolManager (Optimism)
    "0x188d586ddcf52439676ca21a244753fa19f9ea8e": "dex",      # Uniswap v4 PoolManager (Monad)
    "0x238a358808379702088667322f80ac48bad5e6c4": "dex",      # PancakeSwap Infinity Vault (BNB Chain)
}

TOKEN = os.environ.get("ENVIO_API_TOKEN")
if not TOKEN:
    sys.exit("Set ENVIO_API_TOKEN (get one at https://envio.dev/app/api-tokens)")


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read().decode()


def post(url, body, auth=False, tries=10):
    headers = {"Content-Type": "application/json", "User-Agent": "curl/8"}
    if auth:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    for attempt in range(tries):
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except Exception:
            time.sleep(3 * (attempt + 1))
    sys.exit("Request kept failing: " + url)


def rpc(url, method, params):
    return post(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})


def call(url, to, data, block="latest"):
    res = rpc(url, "eth_call", [{"to": to, "data": data}, block])
    return res.get("result")  # None when the call reverts


# 1. Every issuer's CRCL token, from the issuers' own lists
tokens = []  # (issuer, chain, address)
for row in csv.DictReader(io.StringIO(fetch(ONDO_SHEET))):
    if row["Stock Ticker"] == "CRCL":
        for column, chain in (("Ethereum Deployed Address", "Ethereum"), ("BSC Deployed Address", "BNB Chain"),
                              ("HyperEVM Deployed Address", "HyperEVM"), ("Robinhood Chain Deployed Address", "Robinhood")):
            if row[column].strip():
                tokens.append(("Ondo", chain, row[column].strip().lower()))
        ondo_solana = row["Solana Deployed Address"].strip()
page = fetch(XSTOCKS)
products = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S).group(1))
crclx = next(p for p in products["props"]["pageProps"]["products"] if p["symbol"] == "CRCLx")["addresses"]
for key, chain in (("ethereum", "Ethereum"), ("bsc", "BNB Chain"), ("ink", "Ink"), ("arbitrum", "Arbitrum"),
                   ("optimism", "Optimism"), ("mantle", "Mantle"), ("monad", "Monad")):
    if crclx.get(key):
        tokens.append(("xStocks", chain, crclx[key].lower()))
for asset in json.loads(fetch(ROBINHOOD))["assets"]:
    if asset["tokenSymbol"] == "CRCL":
        tokens += [("Robinhood", "Robinhood", d["contractAddress"].lower()) for d in asset["deployments"] if d["chainId"] == 4663]
coinbase = next(t for t in json.loads(fetch(COINBASE + "?page_size=500"))["tokens"] if t["symbol"] == "CRCLc")
tokens.append(("Coinbase", "Base", coinbase["contract_address"].lower()))
bstocks = json.loads(fetch(BSTOCKS))
assert bstocks["symbol"] == "CRCLB"
tokens.append(("Binance bStocks", "BNB Chain", bstocks["id"].lower()))
price = float(coinbase["nav_price"])  # one CRCL price for every token: Coinbase's published NAV for CRCLc

# 2. Replay every Transfer of each EVM token with HyperSync, then sort holders by type
supply = collections.defaultdict(float)  # (issuer, chain) -> shares held outside the issuer's mint wallet
split = collections.Counter()           # holder type -> shares, EVM chains only
code_cache, kind_cache, checks, named = {}, {}, [], {}


def nonzero(result):
    return bool(result) and len(result) >= 66 and int(result[:66], 16) != 0


def kind(chain, holder):
    key = (chain, holder)
    if key in kind_cache:
        return kind_cache[key]
    url = CHAINS[chain][1]
    code = rpc(url, "eth_getCode", [holder, "latest"]).get("result", "0x")
    if code in ("0x", "") or code.startswith("0xef0100"):  # no code, or an EIP-7702 delegated wallet
        k = "wallet"
    elif holder in SINGLETONS:
        k = SINGLETONS[holder]
    elif nonzero(call(url, holder, "0xc45a0155")) and nonzero(call(url, holder, "0x0dfe1681")):
        k = "dex"  # factory() and token0(): Uniswap, PancakeSwap and Aerodrome style pools
    elif nonzero(call(url, holder, "0xb16a19de")):  # UNDERLYING_ASSET_ADDRESS(): Aave style lending tokens
        k = "lending"
    else:
        k = "other contract"
    kind_cache[key] = k
    return k


for issuer, chain, address in tokens:
    slug, url = CHAINS[chain]
    decimals = int(call(url, address, "0x313ce567"), 16)
    body = {"from_block": 0, "logs": [{"address": [address], "topics": [[TRANSFER]]}],
            "field_selection": {"log": ["topic1", "topic2", "data"]}}
    balance = collections.Counter()

    def replay():
        while True:
            res = post(f"https://{slug}.hypersync.xyz/query", body, auth=True)
            for batch in res["data"]:
                for log in batch.get("logs") or []:
                    value = int(log["data"][:66], 16)
                    balance["0x" + log["topic1"][-40:]] -= value
                    balance["0x" + log["topic2"][-40:]] += value
            body["from_block"] = res["next_block"]
            if res["next_block"] >= res["archive_height"]:
                return res["archive_height"] - 1

    # Some public RPCs keep only recent state, so catch up to the tip and read totalSupply() at the last replayed block
    for attempt in range(6):
        block = hex(replay())
        onchain = call(url, address, "0x18160ddd", block)
        if onchain:
            break
    minted = -balance[ZERO]
    checks.append(f"  {issuer} on {chain}: replayed supply {'matches' if minted == int(onchain, 16) else 'DOES NOT MATCH'} "
                  f"totalSupply() at block {int(block, 16):,}")
    balance.pop(ZERO, None)
    held = {h: v for h, v in balance.items() if v > 0}
    if issuer == "xStocks":
        held.pop(XSTOCKS_MINT_WALLET, None)
    total = sum(held.values())
    supply[(issuer, chain)] += total / 10 ** decimals
    if address == bstocks["id"].lower():
        named["Binance Hot Wallet 20"] = held.get(BINANCE_HOT_WALLET_20, 0) / total
    # Classify every holder with at least 0.01% of the token, the rest are counted as wallets
    for h, v in held.items():
        k = kind(chain, h) if v * 10000 >= total else "wallet"
        split[k] += v / 10 ** decimals
    print(f"  read {issuer} {chain}: {total / 10 ** decimals:,.2f} shares, {len(held):,} holders", file=sys.stderr)

# 3. Chains outside HyperSync: X Layer (xStocks) and Solana (xStocks, Ondo)
if crclx.get("xLayer"):
    xl = crclx["xLayer"]
    dec = int(call(XLAYER_RPC, xl, "0x313ce567"), 16)
    total = int(call(XLAYER_RPC, xl, "0x18160ddd"), 16)
    mint_wallet = int(call(XLAYER_RPC, xl, "0x70a08231" + XSTOCKS_MINT_WALLET[2:].rjust(64, "0")), 16)
    supply[("xStocks", "X Layer")] = (total - mint_wallet) / 10 ** dec


def solana_supply(mint):
    return float(rpc(SOLANA_RPC, "getTokenSupply", [mint])["result"]["value"]["uiAmountString"])


minter = rpc(SOLANA_RPC, "getTokenAccountsByOwner", [XSTOCKS_SOLANA_MINTER, {"mint": crclx["solana"]}, {"encoding": "jsonParsed"}])
minter_held = sum(float(a["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmountString"]) for a in minter["result"]["value"])
supply[("xStocks", "Solana")] = solana_supply(crclx["solana"]) - minter_held
supply[("Ondo", "Solana")] = solana_supply(ondo_solana)

# 4. Print
grand = sum(supply.values())
print(f"Tokenized Circle (CRCL) stock onchain: {grand:,.0f} shares, ${grand * price / 1e6:,.1f}M at ${price} (Coinbase CRCLc NAV)")
by_issuer = collections.defaultdict(dict)
for (issuer, chain), v in supply.items():
    by_issuer[issuer][chain] = v
for issuer, chains in sorted(by_issuer.items(), key=lambda kv: -sum(kv[1].values())):
    s = sum(chains.values())
    print(f"  {issuer:16}${s * price / 1e6:7.1f}M  {100 * s / grand:4.1f}%")
    for chain, v in sorted(chains.items(), key=lambda kv: -kv[1]):
        if v * price >= 50_000:
            print(f"      {chain:10}${v * price / 1e6:7.1f}M")
by_chain = collections.Counter()
for (issuer, chain), v in supply.items():
    by_chain[chain] += v
print("By chain: " + ", ".join(f"{c} {100 * v / grand:.1f}%" for c, v in by_chain.most_common() if v * price >= 50_000))
evm = sum(split.values())
print(f"On the EVM chains (${evm * price / 1e6:,.1f}M), by holder type")
for k in ("wallet", "other contract", "dex", "lending"):
    print(f"  {k:15}${split[k] * price / 1e6:7.1f}M  {100 * split[k] / evm:4.1f}%")
print(f"Binance Hot Wallet 20 holds {100 * named['Binance Hot Wallet 20']:.1f}% of Binance's CRCLB")
print("Checks")
print("\n".join(checks))
