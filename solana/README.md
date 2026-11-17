# Solana

Scripts for Solana. Pull every instruction a program runs, every mint and burn of an SPL token, or every token balance change, all with [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana). The HyperIndex indexers further down keep Solana data live behind a GraphQL API.

| Example | Chain | How to |
| --- | --- | --- |
| [phantom-cash-supply](../phantom-cash-supply) | Solana | Track Phantom CASH stablecoin supply week by week |
| [sofiusd-solana](../sofiusd-solana) | Solana | Rebuild SoFiUSD supply on Solana from every mint and burn |
| [huma-payfi-solana](../huma-payfi-solana) | Solana | Pull every Huma Institutional drawdown and repayment on Solana |
| [jupiter-lend-stock-collateral](../jupiter-lend-stock-collateral) | Solana | Pull every Jupiter Lend borrow position, grouped by collateral |
| [backpack-stocks-solana](../backpack-stocks-solana) | Solana | Track Backpack tokenized stock holders, mints and burns on Solana |
| [tokenized-treasuries-solana](tokenized-treasuries-solana) | Solana | Track the supply of tokenized Treasury funds on Solana, day by day |
| [kamino-rwa-collateral](../kamino-rwa-collateral) | Solana | Find real-world credit used as collateral on Kamino Lend |
| [phoenix-perps-signups](../phoenix-perps-signups) | Solana | Track Phoenix trading accounts and USDC deposits on Solana |
| [metadao-launchpad-raises](../metadao-launchpad-raises) | Solana | Pull every MetaDAO launchpad raise on Solana |
| [solana-durable-nonces](solana-durable-nonces) | Solana | Count Solana transactions that use durable nonces |

### Indexers

These HyperIndex indexers keep Solana data live behind a GraphQL API.

| Indexer | Chain | How to |
| --- | --- | --- |
| [solana-dex-swaps-by-program](solana-dex-swaps-by-program) | Solana | Index every swap on Solana's main DEX programs, direct and routed |
| [solana-subscriptions](solana-subscriptions) | Solana | Index every plan, subscription and pull on Solana's Subscriptions program |
| [privacy-rings-solana](privacy-rings-solana) | Solana | Index Privacy Rings deposits, withdrawals and private transfers on Solana |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
