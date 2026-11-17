# Tokenized stocks

Scripts for tokenized stocks. Find everyone holding a stock token, pull every transfer and swap, or see how much trading happens when US markets are shut, all with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

| Example | Chain | How to |
| --- | --- | --- |
| [tokenized-stocks-ethereum](tokenized-stocks-ethereum) | Ethereum | Track every Ondo Global Markets and xStocks token transfer on Ethereum |
| [tokenized-circle-stock](tokenized-circle-stock) | EVM chains | Find tokenized Circle (CRCL) stock on every chain, by issuer |
| [ondo-stocks-by-chain](ondo-stocks-by-chain) | Ethereum, BNB Chain, HyperEVM, Robinhood Chain | Pull every Ondo stock and ETF token transfer, by chain |
| [ondo-stocks-robinhood](ondo-stocks-robinhood) | Robinhood Chain | Pull every Uniswap v4 swap in Ondo tokenized stock pools |
| [uniswap-stock-tokens-after-hours](uniswap-stock-tokens-after-hours) | Robinhood Chain | Split stock token swaps on Uniswap by US market hours |
| [pancakeswap-robinhood-stock-traders](pancakeswap-robinhood-stock-traders) | Robinhood Chain | Count the wallets swapping stock tokens on PancakeSwap |
| [aero-tokenized-stocks-base](aero-tokenized-stocks-base) | Base | Get Coinbase tokenized stock volume on Aero, in and out of market hours |
| [base-tokenized-stock-holders](base-tokenized-stock-holders) | Base | Find every holder of Coinbase tokenized stocks on Base |
| [aave-v4-spcxc-base](aave-v4-spcxc-base) | Base | Track SPCXc holders and the Aave v4 tokenized stocks market on Base |

### Also on Solana

| Example | How to |
| --- | --- |
| [backpack-stocks-solana](../backpack-stocks-solana) | Track Backpack tokenized stock holders, mints and burns on Solana |
| [jupiter-lend-stock-collateral](../jupiter-lend-stock-collateral) | Pull every Jupiter Lend borrow position, grouped by collateral |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
