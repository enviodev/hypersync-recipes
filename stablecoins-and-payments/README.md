# Stablecoins and payments

Scripts for stablecoins and payments. Pull every mint, burn and transfer of a stablecoin, rebuild its supply day by day, or size up onchain payments, all with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

| Example | Chain | How to |
| --- | --- | --- |
| [usdc-supply-ethereum](usdc-supply-ethereum) | Ethereum | Pull every USDC mint and burn on Ethereum and track supply day by day |
| [rlusd-ethereum-supply](rlusd-ethereum-supply) | Ethereum | Rebuild Ripple USD (RLUSD) supply from every mint and burn |
| [arc-usdc-mint-burn](arc-usdc-mint-burn) | Arc | Pull every USDC mint and burn on Arc, including Circle Gateway and CCTP |
| [arc-stablecoins-30d](arc-stablecoins-30d) | Arc | Track USDC and EURC supply on Arc over 30 days |
| [monad-stablecoin-weekends](monad-stablecoin-weekends) | Monad | Pull every stablecoin transfer on Monad and compare weekdays with weekends |
| [ousd-supply-by-chain](ousd-supply-by-chain) | Ethereum, Base, Tempo | Track Open USD (OUSD) supply and holders on each chain |
| [base-usdc-micropayments](base-usdc-micropayments) | Base | Pull every gasless USDC payment on Base and size it down to the cent |
| [uniswap-stable-volume-by-chain](uniswap-stable-volume-by-chain) | 22 EVM chains | Get Uniswap stablecoin-to-stablecoin volume on 22 chains |
| [etherfi-cash-card-payments](../etherfi-cash-card-payments) | Optimism | Pull every ether.fi Cash card payment settled onchain |

### Also on Solana

| Example | How to |
| --- | --- |
| [phantom-cash-supply](../phantom-cash-supply) | Track Phantom CASH stablecoin supply week by week |
| [sofiusd-solana](../sofiusd-solana) | Rebuild SoFiUSD supply on Solana from every mint and burn |
| [huma-payfi-solana](../huma-payfi-solana) | Pull every Huma Institutional drawdown and repayment on Solana |

To run one, grab a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens), export it as `ENVIO_API_TOKEN` and follow that example's README. The [main README](../README.md) has every topic.
