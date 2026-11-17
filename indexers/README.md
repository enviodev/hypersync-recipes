# HyperIndex indexers

HyperIndex indexers that keep the data up to date and serve it over GraphQL. Run them locally, or deploy them on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service) and get a hosted endpoint.

| Indexer | Chain | How to |
| --- | --- | --- |
| [solana-dex-swaps-by-program](solana-dex-swaps-by-program) | Solana | Index every swap on Solana's main DEX programs, direct and routed |
| [solana-subscriptions](solana-subscriptions) | Solana | Index every plan, subscription and pull on Solana's Subscriptions program |
| [privacy-rings-solana](privacy-rings-solana) | Solana | Index Privacy Rings deposits, withdrawals and private transfers on Solana |
| [metamask-money-account](../metamask-money-account) | Monad | Index every MetaMask Money Account deposit, withdrawal and balance |
| [elysium-uniswap-v4-pools](../elysium-uniswap-v4-pools) | Elysium | Index every Uniswap v4 pool on Elysium over RPC |
| [elysium-hype-deposits](../elysium-hype-deposits) | HyperEVM | Index every HYPE deposit into Elysium through its bridge |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
