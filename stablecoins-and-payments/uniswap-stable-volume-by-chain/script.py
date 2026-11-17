"""
Uniswap v3 and v4 swap volume between two USD stablecoins, split by chain,
read with Envio HyperSync.

Usage:
    export ENVIO_API_TOKEN=...            # https://envio.dev/app/api-tokens
    python3 script.py                     # 30 days to 9 Nov 2026 00:00 UTC (the window in the post)
    python3 script.py 1794614400          # 30 days to any unix timestamp
    CHAINS=1,137 python3 script.py        # only some chains

How it counts:
  - A pool counts when both of its tokens are USD stablecoins from the list below.
    Every address was checked onchain with symbol() and decimals().
  - v3: PoolCreated from each chain's UniswapV3Factory, then Swap events from those pools.
  - v4: Initialize from each chain's PoolManager, then Swap events with those pool ids.
  - Factory and PoolManager addresses come from https://developers.uniswap.org/deployments.json
  - Each swap counts once, as abs(amount) of one side, valued at $1. The side is the
    more established coin (USDC, then USDT, then DAI, then USDS), so a coin trading
    off its peg cannot inflate the total.
  - Queries use HyperSync's default join. The script also keeps only logs whose
    address and topic0 match what it asked for.
"""
import json, os, sys, time, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

CHAINS = {
    1: dict(name="Ethereum", v3="0x1F98431c8aD98523631AE4a59f267346ea31F984", v4="0x000000000004444c5dc75cB358380D2e3dE08A90",
        stables={"0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6), "0x6440f144b7e50d6a8439336510312d2f54beb01d": ("BOLD", 18), "0x6b175474e89094c44da98b954eedeac495271d0f": ("DAI", 18), "0xc5f0f7b66764f6ec8c8dff7ba683102295e16409": ("FDUSD", 18), "0x40d16fc0246ad3160ccc09b8d0d3a2cd28ae6c2f": ("GHO", 18), "0x056fd409e1d7a124bd7017459dfea2f387b6d5cd": ("GUSD", 2), "0x5f98805a4e8be255a32880fdec7f6728c6568ba0": ("LUSD", 18), "0x9f6f3991d525015a6f8caf062c83b62fd3ac4436": ("OUSD", 6), "0x6c3ea9036406852006290770bedfcaba0e23a0e8": ("PYUSD", 6), "0x8292bb45bf1ee4d140127049757c2e0ff06317ed": ("RLUSD", 18), "0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d": ("USD1", 18), "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": ("USDC", 6), "0xe343167631d89b6ffc58b88d6b7fb0228795491d": ("USDG", 6), "0x8e870d67f660d95d5be530380d0ec0bd388289e1": ("USDP", 18), "0xc83e27f270cce0a3a3a29521173a83f402c1768b": ("USDQ", 6), "0x7b43e3875440b44613dc3bc08e7763e6da63c8f8": ("USDR", 6), "0xdc035d45d973e3ec169d2276ddab16f1e407384f": ("USDS", 18), "0xdac17f958d2ee523a2206206994597c13d831ec7": ("USDT", 6), "0x4c9edd5852cd905f086c759e8383e09bff1e68b3": ("USDe", 18), "0xc139190f447e929f090edeb554d95abb8b18ac1c": ("USDtb", 18), "0xf939e0a03fb07f59a73314e73794be0e57ac1b4e": ("crvUSD", 18), "0xcacd6fd266af91b8aed52accc382b4e165586e29": ("frxUSD", 18)}),
    10: dict(name="Optimism", v3="0x1F98431c8aD98523631AE4a59f267346ea31F984", v4="0x9a13F98Cb987694C9F086b1F5eB990EeA8264Ec3",
        stables={"0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": ("DAI", 18), "0xc40f949f8a4e094d1b49a23ea9241d289b7b2819": ("LUSD", 18), "0x0b2c639c533813f4aa9d7837caf62653d097ff85": ("USDC", 6), "0x7f5c764cbc14f9669b88837ca1490cca17c31607": ("USDC", 6), "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": ("USDT", 6), "0x01bff41798a0bcf287b996046ca68b395dbc1071": ("USD₮0", 6)}),
    56: dict(name="BNB Chain", v3="0xdB1d10011AD0Ff90774D0C6Bb92e5C5c8b4461F7", v4="0x28e2Ea090877bF75740558f6BFB36A5ffeE9e9dF",
        stables={"0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6), "0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3": ("DAI", 18), "0xc5f0f7b66764f6ec8c8dff7ba683102295e16409": ("FDUSD", 18), "0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d": ("USD1", 18), "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d": ("USDC", 18), "0x55d398326f99059ff775485246999027b3197955": ("USDT", 18), "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": ("USDe", 18)}),
    100: dict(name="Gnosis", v3="0xe32F7dD7e3f098D518ff19A22d5f028e076489B1", v4=None,
        stables={"0xddafbb505ad214d7b80b1f830fccc89b60fb7a83": ("USDC", 6), "0x2a22f9c3b484c3629090feed35f17ff8f88f76f0": ("USDC.e", 6), "0x4ecaba5870353805a9f068101a40e0f32ed605c6": ("USDT", 6), "0xe91d153e0b41518a2ce8dd3d7944fa863463a97d": ("WXDAI", 18)}),
    130: dict(name="Unichain", v3="0x1F98400000000000000000000000000000000003", v4="0x1F98400000000000000000000000000000000004",
        stables={"0x20cab320a855b39f724131c69424240519573f81": ("DAI", 18), "0xeba12ec786cdc21b4bd5ba601b595b6a5c0920a9": ("GUSD", 2), "0xf81b7485b4cb59645f74528d702c7f8cd72577fb": ("LUSD", 18), "0x0d2f98904d88909072ea6e61105cbbf78e6207c5": ("PYUSD", 6), "0x078d782b760474a361dda0af3839290b0ef57ad6": ("USDC", 6), "0x2a22868610610199d43fe93a16661473a9f86f1e": ("USDG", 6), "0xf7e6430137ef8087e0d472343f358e986de0feff": ("USDP", 18), "0xf37748d2cc6e6d5d05945ce130c03c147b2f3a5f": ("USDQ", 6), "0xac025d055a6b633992de1f796b97b97f004c06a7": ("USDR", 6), "0x116ee4d63847fb295dd919ae57b768ea3b2f7bb4": ("USDS", 18), "0x588ce4f028d8e7b53b687865d6a67b3a54c75518": ("USDT", 6), "0x9151434b16b9763660705744891fa906f660ecc5": ("USD₮0", 6)}),
    137: dict(name="Polygon", v3="0x1F98431c8aD98523631AE4a59f267346ea31F984", v4="0x67366782805870060151383F4BbFF9daB53e5cD6",
        stables={"0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6), "0x8f3cf7ad23cd3cadbd9735aff958023239c6a063": ("DAI", 18), "0xc8a94a3d3d2dabc3c1caffffdca6a7543c3e3e65": ("GUSD", 2), "0x23001f892c0c82b79303edc9b9033cd190bb21c7": ("LUSD", 18), "0x6f3b3286fd86d8b47ec737ceb3d0d354cc657b3e": ("PAX", 18), "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": ("USDC", 6), "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": ("USDC", 6), "0xc2132d05d31c914a87c6611c10748aeb04b58e8f": ("USDT0", 6)}),
    143: dict(name="Monad", v3="0x204FAca1764B154221e35c0d20aBb3c525710498", v4="0x188d586Ddcf52439676Ca21A244753fA19F9Ea8e",
        stables={"0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6), "0x754704bc059f8c67012fed69bc8a327a5aafb603": ("USDC", 6), "0xe7cd86e13ac4309349f30b3435a9d337750fc82d": ("USDT0", 6)}),
    146: dict(name="Sonic", v3="0xcb2436774C3e191c85056d248EF4260ce5f27A9D", v4=None,
        stables={"0x29219dd400f2bf60e5a23d13be72b486d4038894": ("USDC", 6), "0x6047828dc181963ba44974801ff68e538da5eaf9": ("USDT", 6)}),
    324: dict(name="ZKsync", v3="0x8FdA5a7a8dCA67BBcDd10F02Fa0649A937215422", v4=None,
        stables={"0x1d17cbcf0d6d143135ae902365d2e5e2a16538d4": ("USDC", 6), "0x3355df6d4c9c3035724fd0e3914de96a5a83aaf4": ("USDC.e", 6), "0x493257fd37edb34451f62edf8d2a0c418852ba4c": ("USDT", 6)}),
    999: dict(name="HyperEVM", v3="0xf0db7b58379503491d857dB50AC9ece64c653918", v4="0x12D4Fd9C5DeDd00ab8a0bCe2CF0167bbf94b6B1F",
        stables={"0xb88339cb7199b77e23db6e890353e22632ba630f": ("USDC", 6), "0x111111a1a0667d36bd57c0a9f569b98057111111": ("USDH", 6), "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": ("USDe", 18), "0xb8ce59fc3717ada4c02eadf9682a9e934f625ebb": ("USD₮0", 6)}),
    1329: dict(name="Sei", v3="0x75FC67473A91335B5b8F8821277262a13B38c9b3", v4=None,
        stables={"0xe15fc38f6d8c56af07bbcbe3baf5708a2bf42392": ("USDC", 6), "0x9151434b16b9763660705744891fa906f660ecc5": ("USD₮0", 6)}),
    1868: dict(name="Soneium", v3="0x42aE7Ec7ff020412639d443E245D936429Fbe717", v4="0x360E68faCcca8cA495c1B759Fd9EEe466db9FB32",
        stables={"0xba9986d2381edf1da03b0b9c1f8b00dc4aacc369": ("USDC.e", 6), "0x3a337a6ada9d885b6ad95ec48f9b75f197b5ae35": ("USDT", 6)}),
    4217: dict(name="Tempo", v3="0x24a3d4757E330890A8b8978028c9e58E04611fd6", v4="0x33620f62C5b9B2086dD6b62F4A297A9f30347029",
        stables={"0x20c0000000000000000000006a37da5c996874be": ("OUSD", 6), "0x20c000000000000000000000b9537d11c60e8b50": ("USDC.e", 6), "0x20c00000000000000000000014f22ca97301eb73": ("USDT0", 6), "0x20c0000000000000000000000000000000000000": ("pathUSD", 6)}),
    5000: dict(name="Mantle", v3="0x0d922Fb1Bc191F64970ac40376643808b4B74Df9", v4=None,
        stables={"0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9": ("USDC", 6), "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae": ("USDT", 6), "0x779ded0c9e1022225f8e0630b35a9b54be713736": ("USDT0", 6), "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": ("USDe", 18)}),
    5042: dict(name="Arc", v3="0xf0db7b58379503491d857dB50AC9ece64c653918", v4="0x8366a39CC670B4001A1121B8F6A443A643e40951",
        stables={"0x3600000000000000000000000000000000000000": ("USDC", 6), "0x0000000000000000000000000000000000000000": ("USDC (native)", 18)}),
    8453: dict(name="Base", v3="0x33128a8fC17869897dcE68Ed026d694621f6FDfD", v4="0x498581fF718922c3f8e6A244956aF099B2652b2b",
        stables={"0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6), "0x50c5725949a6f0c72e6c4a641f24049a917db0cb": ("DAI", 18), "0x368181499736d0c0cc614dbb145e2ec1ac86b8c6": ("LUSD", 18), "0xb2000000000000000000002feb517dfec7415344": ("OUSD", 6), "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": ("USDC", 6), "0x820c137fa70c8691f0e44dc420a5e53c168921dc": ("USDS", 18), "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2": ("USDT", 6), "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca": ("USDbC", 6), "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": ("USDe", 18)}),
    42161: dict(name="Arbitrum", v3="0x1F98431c8aD98523631AE4a59f267346ea31F984", v4="0x360E68faCcca8cA495c1B759Fd9EEe466db9FB32",
        stables={"0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6), "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": ("DAI", 18), "0x93b346b6bc2548da6a1e7d98e9a421b42541425b": ("LUSD", 18), "0x327006c8712fe0abdbbd55b7999db39b0967342e": ("PYUSD", 6), "0x7550de0a4b9fb8caba8c32e72ee356afdd217a33": ("USD1", 18), "0xaf88d065e77c8cc2239327c5edb3a432268e5831": ("USDC", 6), "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": ("USDC", 6), "0x004b506865409877c9fa29bfb1eba929984b9bbc": ("USDG", 6), "0x78df3a6044ce3cb1905500345b967788b699df8f": ("USDP", 18), "0x6491c05a82219b8d1479057361ff1654749b876b": ("USDS", 18), "0x5d3a1ff2b6bab83b63cd9ad0787074081a52ef34": ("USDe", 18), "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": ("USD₮0", 6)}),
    42220: dict(name="Celo", v3="0xAfE208a311B21f13EF87E33A90049fC17A7acDEc", v4="0x288dc841A52FCA2707c6947B3A777c5E56cd87BC",
        stables={"0xceba9300f2b948710d2653dd7b07f33a8b32118c": ("USDC", 6), "0x765de816845861e75a25fca122bb6898b8b1282a": ("USDm", 18), "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e": ("USD₮", 6)}),
    43114: dict(name="Avalanche", v3="0x740b1c1de25031C31FF4fC9A62f554A55cdC1baD", v4="0x06380C0e0912312B5150364B9DC4542BA0DbBc85",
        stables={"0x00000000efe302beaa2b3e6e1b18d08d69a9012a": ("AUSD", 6), "0xd586e7f844cea2f87f50152665bcbc2c279d8d70": ("DAI.e", 18), "0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e": ("USDC", 6), "0xa7d7079b0fead91f3e65f86e8915cb59c1a4c664": ("USDC.e", 6), "0xc7198437980c041c805a1edcba50c1ce5db95118": ("USDT.e", 6), "0x9702230a8ea53601f5cd2dc00fdbc13d4df4a8c7": ("USDt", 6)}),
    57073: dict(name="Ink", v3="0x640887A9ba3A9C53Ed27D0F7e8246A4F933f3424", v4="0x360E68faCcca8cA495c1B759Fd9EEe466db9FB32",
        stables={"0x142cdc44890978b506e745bb3bd11607b7f7faef": ("PYUSD", 6), "0x2d270e6886d130d724215a266106e6832161eaed": ("USDC", 6), "0xf1815bd50389c46847f0bda824ec8da914045d14": ("USDC.e", 6), "0xe343167631d89b6ffc58b88d6b7fb0228795491d": ("USDG", 6), "0x0200c29006150606b650577bbe7b6248f58470c1": ("USD₮0", 6)}),
    59144: dict(name="Linea", v3="0x31FAfd4889FA1269F7a13A66eE0fB458f27D72A9", v4="0x248083Fb965359d82b06C1F5322480Dcfc1AD857",
        stables={"0x176211869ca2b568f2a7d4ee941e073a821ee1ff": ("USDC", 6), "0xa219439258ca9da29e9cc4ce5596924745e12b93": ("USDT", 6)}),
    534352: dict(name="Scroll", v3="0x70C62C8b8e801124A4Aa81ce07b637A3e83cb919", v4=None,
        stables={"0x06efdbff2a14a7c8e15944d1f4a48f9f95f663a4": ("USDC", 6), "0xf55bec9cafdbe8730f096aa55dad6d22d44099df": ("USDT", 6)}),
}

POOL_CREATED = "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118"
SWAP_V3 = "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"
INITIALIZE_V4 = "0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438"
SWAP_V4 = "0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f"
PRIORITY = ["USDC", "USDT", "USD\u20ae0", "USDT0", "USD\u20ae", "USDt", "USDC.e", "USDT.e", "DAI", "USDS"]

HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["ENVIO_API_TOKEN"]}
END = int(sys.argv[1]) if len(sys.argv) > 1 else int(datetime(2026, 11, 9, tzinfo=timezone.utc).timestamp())
START = END - 30 * 86400


def query(chain, body):
    for attempt in range(8):
        try:
            req = urllib.request.Request(f"https://{chain}.hypersync.xyz/query", json.dumps(body).encode(), HEADERS)
            return json.load(urllib.request.urlopen(req, timeout=300))
        except Exception:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"HyperSync query failed on chain {chain}")


def height(chain):
    req = urllib.request.Request(f"https://{chain}.hypersync.xyz/height", headers=HEADERS)
    return json.load(urllib.request.urlopen(req))["height"]


def num(x):
    return int(x, 16) if isinstance(x, str) else x


def block_at(chain, ts):
    """First block at or after a unix timestamp (binary search on block timestamps)."""
    lo, hi = 0, height(chain) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        r = query(chain, {"from_block": mid, "to_block": mid + 1, "include_all_blocks": True,
                          "field_selection": {"block": ["number", "timestamp"]}})
        if num(r["data"][0]["blocks"][0]["timestamp"]) < ts:
            lo = mid
        else:
            hi = mid
    return hi


def logs(chain, body):
    """Page through a log query until to_block (or the chain head)."""
    out, start, end = [], body["from_block"], body.get("to_block")
    while True:
        body["from_block"] = start
        r = query(chain, body)
        for d in r["data"]:
            out += d.get("logs") or []
        nxt = r["next_block"]
        if nxt <= start or (end and nxt >= end) or nxt >= r.get("archive_height", nxt):
            return out
        start = nxt


def topic(addr):
    return "0x" + "0" * 24 + addr[2:].lower()


def signed(word):
    v = int(word, 16)
    return v - (1 << 256) if v >= 1 << 255 else v


def rank(symbol):
    return PRIORITY.index(symbol) if symbol in PRIORITY else 99


def run(chain):
    cfg = CHAINS[chain]
    stables = cfg["stables"]
    topics = [topic(a) for a in stables]
    b0, b1 = block_at(chain, START), block_at(chain, END)

    pools = {}  # v3 pool address or v4 pool id -> (version, token0, token1)
    if cfg["v3"]:
        factory = cfg["v3"].lower()
        for l in logs(chain, {"from_block": 0, "logs": [{"address": [factory], "topics": [[POOL_CREATED], topics, topics]}],
                              "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "data"]}}):
            if l["address"].lower() == factory and l["topic0"] == POOL_CREATED:
                pools["0x" + l["data"][-40:]] = ("v3", "0x" + l["topic1"][-40:], "0x" + l["topic2"][-40:])
    if cfg["v4"]:
        manager = cfg["v4"].lower()
        for l in logs(chain, {"from_block": 0, "logs": [{"address": [manager], "topics": [[INITIALIZE_V4], [], topics, topics]}],
                              "field_selection": {"log": ["address", "topic0", "topic1", "topic2", "topic3"]}}):
            if l["address"].lower() == manager and l["topic0"] == INITIALIZE_V4:
                pools[l["topic1"]] = ("v4", "0x" + l["topic2"][-40:], "0x" + l["topic3"][-40:])

    volume = {"v3": 0.0, "v4": 0.0}
    swaps = {"v3": 0, "v4": 0}
    by_pool = defaultdict(float)

    def add(key, data):
        version, t0, t1 = pools[key]
        (s0, d0), (s1, d1) = stables[t0], stables[t1]
        a0, a1 = signed(data[2:66]), signed(data[66:130])
        usd = abs(a0) / 10 ** d0 if rank(s0) <= rank(s1) else abs(a1) / 10 ** d1
        volume[version] += usd
        swaps[version] += 1
        by_pool[key] += usd

    fields = {"log": ["address", "topic0", "topic1", "data"]}
    v3_pools = [k for k, p in pools.items() if p[0] == "v3"]
    v4_ids = [k for k, p in pools.items() if p[0] == "v4"]
    for i in range(0, len(v3_pools), 1000):
        chunk = set(v3_pools[i:i + 1000])
        for l in logs(chain, {"from_block": b0, "to_block": b1, "field_selection": fields,
                              "logs": [{"address": list(chunk), "topics": [[SWAP_V3]]}]}):
            if l["address"].lower() in chunk and l["topic0"] == SWAP_V3:
                add(l["address"].lower(), l["data"])
    for i in range(0, len(v4_ids), 1000):
        chunk = set(v4_ids[i:i + 1000])
        manager = cfg["v4"].lower()
        for l in logs(chain, {"from_block": b0, "to_block": b1, "field_selection": fields,
                              "logs": [{"address": [manager], "topics": [[SWAP_V4], list(chunk)]}]}):
            if l["address"].lower() == manager and l["topic0"] == SWAP_V4 and l["topic1"] in chunk:
                add(l["topic1"], l["data"])

    top = sorted(by_pool.items(), key=lambda x: -x[1])[:3]
    return chain, volume, swaps, [(pools[k][0], stables[pools[k][1]][0], stables[pools[k][2]][0], v) for k, v in top]


def short(v):
    return f"${v / 1e9:,.2f}B" if v >= 1e9 else f"${v / 1e6:,.1f}M"


if __name__ == "__main__":
    wanted = [int(x) for x in os.environ.get("CHAINS", "").split(",") if x] or list(CHAINS)
    print(f"Window {datetime.fromtimestamp(START, timezone.utc):%Y-%m-%d %H:%M} to "
          f"{datetime.fromtimestamp(END, timezone.utc):%Y-%m-%d %H:%M} UTC, {len(wanted)} chains\n")
    results = {}
    with ThreadPoolExecutor(6) as ex:
        for f in as_completed([ex.submit(run, c) for c in wanted]):
            chain, volume, swaps, top = f.result()
            results[chain] = (volume, swaps, top)
            print(f"  done {CHAINS[chain]['name']}", flush=True)

    total = sum(sum(v.values()) for v, _, _ in results.values())
    v4 = sum(v["v4"] for v, _, _ in results.values())
    print(f"\nStable-to-stable volume on Uniswap v3 and v4: {short(total)} ({v4 / total:.0%} on v4)\n")
    for chain, (volume, swaps, top) in sorted(results.items(), key=lambda x: -sum(x[1][0].values())):
        t = sum(volume.values())
        if t < 1e5:
            continue
        print(f"{CHAINS[chain]['name']:<12} {short(t):>10} {t / total:6.1%}   v4 {short(volume['v4']):>10}  v3 {short(volume['v3']):>9}"
              f"   {swaps['v3'] + swaps['v4']:>9,} swaps")
        for version, s0, s1, v in top:
            print(f"{'':<14}{version} {s0}/{s1} {short(v)}")
