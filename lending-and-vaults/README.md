# Lending and vaults

Scripts for lending markets and vaults. Pull every supply, borrow, repay and withdrawal on Aave and Morpho, all with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

| Example | Chain | How to |
| --- | --- | --- |
| [aave-monad-tvl](aave-monad-tvl) | Monad | Get Aave v3 TVL on Monad by asset from every transfer |
| [aave-usdc-ethereum-weekly](aave-usdc-ethereum-weekly) | Ethereum | Track weekly USDC deposits and borrows on Aave V3 Ethereum |
| [aave-v4-avalanche](aave-v4-avalanche) | Avalanche | Pull every Aave v4 deposit on Avalanche, by asset and depositor |
| [aave-v4-sentora-markets](aave-v4-sentora-markets) | Ethereum | Track supply and borrows in Sentora's Aave v4 markets, day by day |
| [coinbase-borrow-morpho-base](coinbase-borrow-morpho-base) | Base | Track the Morpho markets behind Coinbase's crypto-backed loans |
| [morpho-midnight-loans](morpho-midnight-loans) | Five chains | Pull every fixed-rate loan on Morpho Midnight |
| [morpho-vaults-arc](morpho-vaults-arc) | Arc | Find every Morpho vault on Arc and the markets it lends to |
| [usdg-on-morpho](usdg-on-morpho) | Robinhood Chain, Arbitrum, Ethereum | Find every Morpho market lending Paxos USDG |
| [robinhood-earn-usdg-vault](robinhood-earn-usdg-vault) | Robinhood Chain | Count depositors in the USDG vault behind Robinhood Earn |

### Also on Solana

| Example | How to |
| --- | --- |
| [jupiter-lend-stock-collateral](../jupiter-lend-stock-collateral) | Pull every Jupiter Lend borrow position, grouped by collateral |
| [kamino-rwa-collateral](../kamino-rwa-collateral) | Find real-world credit used as collateral on Kamino Lend |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
