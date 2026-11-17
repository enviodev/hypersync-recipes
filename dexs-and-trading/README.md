# DEXs, perps and prediction markets

Scripts for DEXs, perps and prediction markets. Pull every swap, pool and position on Uniswap, Aero, Ostium, Polymarket and more, all with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

| Example | Chain | How to |
| --- | --- | --- |
| [uniswap-robinhood-chain](uniswap-robinhood-chain) | Robinhood Chain | Pull every Uniswap v2, v3 and v4 swap on Robinhood Chain |
| [uniswap-volatilepair-robinhood](uniswap-volatilepair-robinhood) | Robinhood Chain | Get swaps, volume and LP fees for one Uniswap pool |
| [uniswap-v4-hooks-ethereum](uniswap-v4-hooks-ethereum) | Ethereum | Find every Uniswap v4 pool with a hook on Ethereum |
| [uniswap-v4-hooks-robinhood](uniswap-v4-hooks-robinhood) | Robinhood Chain | Find every Uniswap v4 pool and swap by hook |
| [aero-pools-arbitrum](aero-pools-arbitrum) | Arbitrum | Rank every Aero pool on Arbitrum by volume and liquidity |
| [1inch-aqua-strategies](1inch-aqua-strategies) | 15 EVM chains | Pull every strategy created on 1inch Aqua |
| [aero-robinhood-ethereum](../aero-robinhood-ethereum) | Robinhood Chain, Ethereum | Track Aero DEX volume day by day on two chains |
| [yieldbasis-weth-propamm](yieldbasis-weth-propamm) | Ethereum | Compare Yield Basis pool volume and fees before and after oracle pricing |
| [metric-first-month-ethereum](../metric-first-month-ethereum) | Ethereum | Pull every swap on Metric's pools, per day |
| [ostium-markets-arbitrum](ostium-markets-arbitrum) | Arbitrum | Pull every Ostium position and group it by market |
| [polymarket-election-day](polymarket-election-day) | Polygon | Get Polymarket trading volume by hour on US election day |
| [polymarket-election-night](polymarket-election-night) | Polygon | Get Polymarket trading volume hour by hour on US election night |

### Also on Solana

| Example | How to |
| --- | --- |
| [phoenix-perps-signups](../phoenix-perps-signups) | Track Phoenix trading accounts and USDC deposits on Solana |
| [metadao-launchpad-raises](../metadao-launchpad-raises) | Pull every MetaDAO launchpad raise on Solana |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
