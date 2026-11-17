# Tokenized funds and real-world assets

Scripts for tokenized funds and real-world assets. Track Treasury funds, money market funds and other RWAs from every mint, burn and transfer, all with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

| Example | Chain | How to |
| --- | --- | --- |
| [blackrock-buidl-by-chain](blackrock-buidl-by-chain) | EVM chains | Track BlackRock BUIDL supply on each chain from every mint and burn |
| [ondo-intelligent-portfolios](ondo-intelligent-portfolios) | Ethereum, BNB Chain | Track Ondo Intelligent Portfolios supply and holders |
| [spiko-safo](spiko-safo) | Ethereum, Arbitrum, Polygon, Base | Track Spiko SAFO supply and holders by chain and share class |
| [grove-basin-jtrsy](grove-basin-jtrsy) | Ethereum | Pull every Grove Basin swap of JTRSY into USDC |
| [paxg-on-morpho-base](paxg-on-morpho-base) | Base | Track USDC borrowed against Paxos Gold (PAXG) on Morpho |

### Also on Solana

| Example | How to |
| --- | --- |
| [tokenized-treasuries-solana](../solana/tokenized-treasuries-solana) | Track the supply of tokenized Treasury funds on Solana, day by day |
| [kamino-rwa-collateral](../kamino-rwa-collateral) | Find real-world credit used as collateral on Kamino Lend |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
