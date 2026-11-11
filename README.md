# HyperSync recipes

Ready-to-run scripts behind Envio's data posts. Each folder reads public onchain data with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), prints the numbers from the post, and includes a prompt you can hand to a coding agent.

| Recipe | Chain | What it shows |
|---|---|---|
| [polymarket-election-day](polymarket-election-day) | Polygon | Polymarket trading by hour on US election day |
| [polymarket-election-night](polymarket-election-night) | Polygon | Polymarket trading hour by hour on US election night, against a normal night |
| [arc-usdc-mint-burn](arc-usdc-mint-burn) | Arc | USDC minted and burned on Arc, and how much went through Circle Gateway and CCTP |
| [uniswap-robinhood-chain](uniswap-robinhood-chain) | Robinhood Chain | Every Uniswap v2, v3 and v4 swap, milestones and stock tokens traded |
| [uniswap-volatilepair-robinhood](uniswap-volatilepair-robinhood) | Robinhood Chain | Swaps, USDG volume and LP fees in Uniswap's VolatilePair pool |
| [ondo-stocks-robinhood](ondo-stocks-robinhood) | Robinhood Chain | Uniswap v4 swaps in Ondo tokenized stock pools, first week |
| [uni-new-holders](uni-new-holders) | Ethereum | New UNI holders per day since 2020 |
| [uniswap-v4-hooks-ethereum](uniswap-v4-hooks-ethereum) | Ethereum | Uniswap v4 pools with a hook, month by month |
| [aave-v4-avalanche](aave-v4-avalanche) | Avalanche | Aave v4 deposits by asset, depositors and the biggest day |
| [usdg-on-morpho](usdg-on-morpho) | Robinhood Chain, Arbitrum, Ethereum | Every USDG market on Morpho and how much is supplied to each |
| [aero-tokenized-stocks-base](aero-tokenized-stocks-base) | Base | Tokenized stock trading on Aero, inside and outside US market hours |
| [ondo-intelligent-portfolios](ondo-intelligent-portfolios) | Ethereum, BNB Chain | Ondo Intelligent Portfolios supply by portfolio and when it arrived |
| [usdc-supply-ethereum](usdc-supply-ethereum) | Ethereum | USDC minted and burned on Ethereum per day |
| [aave-monad-tvl](aave-monad-tvl) | Monad | What makes up the assets held in Aave's Monad pools |
| [spiko-safo](spiko-safo) | Ethereum, Arbitrum, Polygon, Base | Spiko SAFO supply by chain and currency, with holders |
| [tokenized-stocks-ethereum](tokenized-stocks-ethereum) | Ethereum | Which Ondo and xStocks stock tokens move the most on Ethereum |
| [tokenized-treasuries-solana](tokenized-treasuries-solana) | Solana | Supply of the five biggest tokenized Treasury funds, day by day |
| [privacy-rings-solana](privacy-rings-solana) | Solana | A HyperIndex indexer for Helius Privacy Rings: registrations, deposits, withdrawals and private transfers, live |
| [solana-subscriptions](solana-subscriptions) | Solana | A HyperIndex indexer for Solana Subscriptions: subscriptions, plan pulls and allowance pulls, with Helius's USDC pulled since launch |

## Before you start

Get a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens) and export it:

```bash
export ENVIO_API_TOKEN=your-token
```

Then follow the README in the recipe's folder.
