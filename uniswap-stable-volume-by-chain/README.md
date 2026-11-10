# Uniswap stable-to-stable volume by chain

Reads every Uniswap v3 and v4 swap between two USD stablecoins on 22 EVM chains, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and splits the volume by chain and by Uniswap version.

These are the numbers behind Envio's post on where Uniswap's stablecoin-to-stablecoin volume actually settles. Over the 30 days to 9 November 2026 we found $13.9B, and $11.9B of it (86%) was on Ethereum.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a unix timestamp to end the 30-day window somewhere else, and set `CHAINS` to run a subset:

```bash
python script.py 1794614400
CHAINS=1,137 python script.py
```

The full run reads pool creation events from the start of each chain, so it takes a while on chains with long histories such as Arbitrum and BNB Chain.

## What it prints

```
Stable-to-stable volume on Uniswap v3 and v4: $13.88B (92% on v4)

Ethereum        $11.89B  85.6%   v4    $11.00B  v3   $886.4M     473,613 swaps
              v4 USDC/USDT $3.44B
              v4 USDT/USDS $2.24B
              v4 USDC/USDT $1.57B
Polygon         $853.6M   6.1%   v4    $729.9M  v3   $123.7M     537,290 swaps
              v4 USDC/USDT0 $292.8M
              v4 USDC/USDC $238.4M
              v4 DAI/USDT0 $119.7M
BNB Chain       $510.0M   3.7%   v4    $498.9M  v3    $11.0M   1,467,159 swaps
              v4 USDT/USDC $238.5M
              v4 USDT/USDC $171.5M
              v4 USDT/USDC $63.2M
Arbitrum        $324.3M   2.3%   v4    $253.8M  v3    $70.5M     170,454 swaps
              v4 USDC/USD₮0 $227.1M
              v3 USDC/USD₮0 $62.1M
              v4 USDG/USDC $14.2M
Base            $232.5M   1.7%   v4    $210.1M  v3    $22.4M   1,111,945 swaps
              v4 USDC/USDT $64.9M
              v4 USDC/USDT $62.1M
              v4 USDC/USDT $37.9M
Monad            $35.8M   0.3%   v4     $35.3M  v3     $0.5M     157,496 swaps
              v4 AUSD/USDC $30.8M
              v4 AUSD/USDC $1.7M
              v4 AUSD/USDC $1.2M
...
```

## How it counts

- Factory and PoolManager addresses come from Uniswap's official [deployments list](https://developers.uniswap.org/deployments.json).
- A pool counts when both of its tokens are USD stablecoins: USDC (native and bridged), USDT and USDT0, DAI, USDS, USDe, PYUSD, USD1, RLUSD, USDG, FDUSD, GHO, AUSD, USDtb, frxUSD, crvUSD, LUSD, BOLD and a few smaller ones. Addresses come from Uniswap's default token list and the issuers, and all but Arc's native USDC were checked onchain with `symbol()` and `decimals()`. Euro stablecoins and yield-bearing tokens such as sUSDe are left out.
- v3 pools come from `PoolCreated` on each chain's factory, filtered to stablecoins on both sides. v4 pools come from `Initialize` on each chain's PoolManager, filtered the same way.
- Each swap counts once, as the absolute amount of one side at $1. The script takes the more established coin's side (USDC, then USDT, then DAI, then USDS), so a smaller coin trading off its peg cannot inflate the total.
- The queries use HyperSync's default join, so only the matching logs come back. The script also keeps only logs whose address and topic0 match what it asked for.
- Uniswap v2 is not included, and neither are chains HyperSync does not index, such as X Layer.

## Checks we ran

- 32 swaps, sampled across Ethereum, Polygon, BNB Chain, Arbitrum, Base and Monad, were decoded again from transaction receipts on public RPC endpoints. Every one matched to the cent.
- Uniswap reported $15B+ of stable-to-stable volume on EVM chains for the same 30 days. This script finds $13.9B on v3 and v4, about 93% of that. The difference is likely v2 pools, chains outside this list, and where exactly the 30 days start and end.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to find every Uniswap v3
and v4 pool where both tokens are USD stablecoins, on Ethereum, Polygon, BNB Chain, Arbitrum and
Base. Use PoolCreated from the v3 factory and Initialize from the v4 PoolManager, with addresses
from https://developers.uniswap.org/deployments.json. Then sum the USD volume of their Swap
events over the last 30 days, by chain and by version. My API token is in the ENVIO_API_TOKEN
environment variable.
```

## Learn more

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Index Ethereum with Envio](https://envio.dev/chains/ethereum)
- [HyperIndex, for a full indexer with a GraphQL API](https://docs.envio.dev/docs/HyperIndex/overview)
