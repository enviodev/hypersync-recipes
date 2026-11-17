# HyperIndex indexers

HyperIndex indexers that keep onchain data up to date and serve it as a GraphQL API. Run them locally or deploy them on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

| Indexer | Chain | How to |
| --- | --- | --- |
| [solana-dex-swaps-by-program](solana-dex-swaps-by-program) | Solana | Index every swap on Solana's main DEX programs, direct and routed |
| [solana-subscriptions](solana-subscriptions) | Solana | Index every plan, subscription and pull on Solana's Subscriptions program |
| [privacy-rings-solana](privacy-rings-solana) | Solana | Index Privacy Rings deposits, withdrawals and private transfers on Solana |
| [metamask-money-account](../metamask-money-account) | Monad | Index every MetaMask Money Account deposit, withdrawal and balance |
| [elysium-uniswap-v4-pools](../elysium-uniswap-v4-pools) | Elysium | Index every Uniswap v4 pool on Elysium over RPC |
| [elysium-hype-deposits](../elysium-hype-deposits) | HyperEVM | Index every HYPE deposit into Elysium through its bridge |

To run any of them, get a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow the example's README. See the [full list of examples](../README.md) for every topic.
