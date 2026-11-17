# HyperSync examples

Curated, ready-to-run scripts that pull onchain data with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Each one answers a real question, like how much USDC was minted on Ethereum this week or who holds a tokenized stock, and prints the answer in your terminal.

Pick the one closest to what you need, swap in your contract, chain or dates, and you've got the start of your own dashboard, backfill or pipeline. Each one also has a prompt you can paste into Claude Code or Cursor if you'd rather your agent did the editing.

- **74 examples** across Ethereum, Base, Arbitrum, Optimism, Polygon, BNB Chain, Avalanche, Monad, Gnosis, Ink, Arc, Robinhood Chain, HyperEVM, Tempo and Solana.
- **Plain Python.** Standard library only, so there's nothing to install and no node to run.
- **A few HyperIndex indexers** for when you want the data live behind a GraphQL API.

## Quick start

1. Get a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).
2. Clone the repo and run one.

```bash
git clone https://github.com/enviodev/hypersync-recipes.git
cd hypersync-recipes/stablecoins-and-payments/usdc-supply-ethereum
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Every folder has its own README with what we found, what the script pulls, how to point it at another chain or window, and how to check the numbers.

## Examples

### Stablecoins and payments

| Example | Chain | How to |
| --- | --- | --- |
| [usdc-supply-ethereum](stablecoins-and-payments/usdc-supply-ethereum) | Ethereum | Pull every USDC mint and burn on Ethereum and track supply day by day |
| [rlusd-ethereum-supply](stablecoins-and-payments/rlusd-ethereum-supply) | Ethereum | Rebuild Ripple USD (RLUSD) supply from every mint and burn |
| [arc-usdc-mint-burn](stablecoins-and-payments/arc-usdc-mint-burn) | Arc | Pull every USDC mint and burn on Arc, including Circle Gateway and CCTP |
| [arc-stablecoins-30d](stablecoins-and-payments/arc-stablecoins-30d) | Arc | Track USDC and EURC supply on Arc over 30 days |
| [monad-stablecoin-weekends](stablecoins-and-payments/monad-stablecoin-weekends) | Monad | Pull every stablecoin transfer on Monad and compare weekdays with weekends |
| [ousd-supply-by-chain](stablecoins-and-payments/ousd-supply-by-chain) | Ethereum, Base, Tempo | Track Open USD (OUSD) supply and holders on each chain |
| [base-usdc-micropayments](stablecoins-and-payments/base-usdc-micropayments) | Base | Pull every gasless USDC payment on Base and size it down to the cent |
| [uniswap-stable-volume-by-chain](stablecoins-and-payments/uniswap-stable-volume-by-chain) | 22 EVM chains | Get Uniswap stablecoin-to-stablecoin volume on 22 chains |
| [etherfi-cash-card-payments](etherfi-cash-card-payments) | Optimism | Pull every ether.fi Cash card payment settled onchain |

### Tokenized stocks

| Example | Chain | How to |
| --- | --- | --- |
| [tokenized-stocks-ethereum](tokenized-stocks/tokenized-stocks-ethereum) | Ethereum | Track every Ondo Global Markets and xStocks token transfer on Ethereum |
| [tokenized-circle-stock](tokenized-stocks/tokenized-circle-stock) | EVM chains | Find tokenized Circle (CRCL) stock on every chain, by issuer |
| [ondo-stocks-by-chain](tokenized-stocks/ondo-stocks-by-chain) | Ethereum, BNB Chain, HyperEVM, Robinhood Chain | Pull every Ondo stock and ETF token transfer, by chain |
| [ondo-stocks-robinhood](tokenized-stocks/ondo-stocks-robinhood) | Robinhood Chain | Pull every Uniswap v4 swap in Ondo tokenized stock pools |
| [uniswap-stock-tokens-after-hours](tokenized-stocks/uniswap-stock-tokens-after-hours) | Robinhood Chain | Split stock token swaps on Uniswap by US market hours |
| [pancakeswap-robinhood-stock-traders](tokenized-stocks/pancakeswap-robinhood-stock-traders) | Robinhood Chain | Count the wallets swapping stock tokens on PancakeSwap |
| [aero-tokenized-stocks-base](tokenized-stocks/aero-tokenized-stocks-base) | Base | Get Coinbase tokenized stock volume on Aero, in and out of market hours |
| [base-tokenized-stock-holders](tokenized-stocks/base-tokenized-stock-holders) | Base | Find every holder of Coinbase tokenized stocks on Base |
| [aave-v4-spcxc-base](tokenized-stocks/aave-v4-spcxc-base) | Base | Track SPCXc holders and the Aave v4 tokenized stocks market on Base |

### Tokenized funds and real-world assets

| Example | Chain | How to |
| --- | --- | --- |
| [blackrock-buidl-by-chain](rwa-and-funds/blackrock-buidl-by-chain) | EVM chains | Track BlackRock BUIDL supply on each chain from every mint and burn |
| [ondo-intelligent-portfolios](rwa-and-funds/ondo-intelligent-portfolios) | Ethereum, BNB Chain | Track Ondo Intelligent Portfolios supply and holders |
| [spiko-safo](rwa-and-funds/spiko-safo) | Ethereum, Arbitrum, Polygon, Base | Track Spiko SAFO supply and holders by chain and share class |
| [grove-basin-jtrsy](rwa-and-funds/grove-basin-jtrsy) | Ethereum | Pull every Grove Basin swap of JTRSY into USDC |
| [pendle-strcx](rwa-and-funds/pendle-strcx) | Ethereum | Find every STRCx holder and how much sits in Pendle |
| [paxg-on-morpho-base](rwa-and-funds/paxg-on-morpho-base) | Base | Track USDC borrowed against Paxos Gold (PAXG) on Morpho |

### Lending and vaults

| Example | Chain | How to |
| --- | --- | --- |
| [aave-monad-tvl](lending-and-vaults/aave-monad-tvl) | Monad | Get Aave v3 TVL on Monad by asset from every transfer |
| [aave-usdc-ethereum-weekly](lending-and-vaults/aave-usdc-ethereum-weekly) | Ethereum | Track weekly USDC deposits and borrows on Aave V3 Ethereum |
| [aave-v4-avalanche](lending-and-vaults/aave-v4-avalanche) | Avalanche | Pull every Aave v4 deposit on Avalanche, by asset and depositor |
| [aave-v4-sentora-markets](lending-and-vaults/aave-v4-sentora-markets) | Ethereum | Track supply and borrows in Sentora's Aave v4 markets, day by day |
| [coinbase-borrow-morpho-base](lending-and-vaults/coinbase-borrow-morpho-base) | Base | Track the Morpho markets behind Coinbase's crypto-backed loans |
| [morpho-midnight-loans](lending-and-vaults/morpho-midnight-loans) | Five chains | Pull every fixed-rate loan on Morpho Midnight |
| [morpho-vaults-arc](lending-and-vaults/morpho-vaults-arc) | Arc | Find every Morpho vault on Arc and the markets it lends to |
| [usdg-on-morpho](lending-and-vaults/usdg-on-morpho) | Robinhood Chain, Arbitrum, Ethereum | Find every Morpho market lending Paxos USDG |
| [robinhood-earn-usdg-vault](lending-and-vaults/robinhood-earn-usdg-vault) | Robinhood Chain | Count depositors in the USDG vault behind Robinhood Earn |
| [safenet-staking](lending-and-vaults/safenet-staking) | Ethereum | Track SAFE staked in Safenet and active stakers week by week |

### DEXs, perps and prediction markets

| Example | Chain | How to |
| --- | --- | --- |
| [uniswap-robinhood-chain](dexs-and-trading/uniswap-robinhood-chain) | Robinhood Chain | Pull every Uniswap v2, v3 and v4 swap on Robinhood Chain |
| [uniswap-volatilepair-robinhood](dexs-and-trading/uniswap-volatilepair-robinhood) | Robinhood Chain | Get swaps, volume and LP fees for one Uniswap pool |
| [uniswap-v4-hooks-ethereum](dexs-and-trading/uniswap-v4-hooks-ethereum) | Ethereum | Find every Uniswap v4 pool with a hook on Ethereum |
| [uniswap-v4-hooks-robinhood](dexs-and-trading/uniswap-v4-hooks-robinhood) | Robinhood Chain | Find every Uniswap v4 pool and swap by hook |
| [aero-pools-arbitrum](dexs-and-trading/aero-pools-arbitrum) | Arbitrum | Rank every Aero pool on Arbitrum by volume and liquidity |
| [aero-robinhood-ethereum](aero-robinhood-ethereum) | Robinhood Chain, Ethereum | Track Aero DEX volume day by day on two chains |
| [yieldbasis-weth-propamm](dexs-and-trading/yieldbasis-weth-propamm) | Ethereum | Compare Yield Basis pool volume and fees before and after oracle pricing |
| [metric-first-month-ethereum](metric-first-month-ethereum) | Ethereum | Pull every swap on Metric's pools, per day |
| [ostium-markets-arbitrum](dexs-and-trading/ostium-markets-arbitrum) | Arbitrum | Pull every Ostium position and group it by market |
| [polymarket-election-day](dexs-and-trading/polymarket-election-day) | Polygon | Get Polymarket trading volume by hour on US election day |
| [polymarket-election-night](dexs-and-trading/polymarket-election-night) | Polygon | Get Polymarket trading volume hour by hour on US election night |

### Chain activity, wallets and accounts

| Example | Chain | How to |
| --- | --- | --- |
| [active-addresses-without-dusting](chain-activity/active-addresses-without-dusting) | EVM chains | Count daily active addresses with dusting filtered out |
| [monad-biggest-apps](chain-activity/monad-biggest-apps) | Monad | Rank Monad apps by transactions over 30 days |
| [monad-volatility-day](chain-activity/monad-volatility-day) | Monad | Compare one day on Monad with a 30-day baseline, hour by hour |
| [gnosis-biggest-protocols](chain-activity/gnosis-biggest-protocols) | Gnosis | Rank the busiest protocols on Gnosis Chain |
| [ink-monthly-activity](chain-activity/ink-monthly-activity) | Ink | Count Ink transactions and active addresses by month |
| [polygon-october-fees](chain-activity/polygon-october-fees) | Polygon | Find which contracts paid the most gas on Polygon PoS |
| [arbitrum-priority-fees](arbitrum-priority-fees) | Arbitrum | Count Arbitrum transactions paying a priority fee, day by day |
| [erc4337-user-operations-ethereum](erc4337-user-operations-ethereum) | Ethereum | Pull every ERC-4337 user operation on Ethereum |
| [ethereum-approval-cleanups](chain-activity/ethereum-approval-cleanups) | Ethereum | Find every ERC-20 approval revoked on Ethereum |
| [safe-growth](chain-activity/safe-growth) | 14 chains | Count every Safe created, by month and chain |
| [safe-shared-signer](chain-activity/safe-shared-signer) | Ethereum | Decode every new Safe's owners and find the most common signer |
| [circles-trust-gnosis](chain-activity/circles-trust-gnosis) | Gnosis | Count Circles v2 humans and trust links on Gnosis Chain |
| [uni-new-holders](chain-activity/uni-new-holders) | Ethereum | Count new UNI holders per day since 2020 |

### Solana

| Example | Chain | How to |
| --- | --- | --- |
| [phantom-cash-supply](phantom-cash-supply) | Solana | Track Phantom CASH stablecoin supply week by week |
| [sofiusd-solana](sofiusd-solana) | Solana | Rebuild SoFiUSD supply on Solana from every mint and burn |
| [huma-payfi-solana](huma-payfi-solana) | Solana | Pull every Huma Institutional drawdown and repayment on Solana |
| [jupiter-lend-stock-collateral](jupiter-lend-stock-collateral) | Solana | Pull every Jupiter Lend borrow position, grouped by collateral |
| [backpack-stocks-solana](backpack-stocks-solana) | Solana | Track Backpack tokenized stock holders, mints and burns on Solana |
| [tokenized-treasuries-solana](solana/tokenized-treasuries-solana) | Solana | Track the supply of tokenized Treasury funds on Solana, day by day |
| [kamino-rwa-collateral](kamino-rwa-collateral) | Solana | Find real-world credit used as collateral on Kamino Lend |
| [phoenix-perps-signups](phoenix-perps-signups) | Solana | Track Phoenix trading accounts and USDC deposits on Solana |
| [metadao-launchpad-raises](metadao-launchpad-raises) | Solana | Pull every MetaDAO launchpad raise on Solana |
| [solana-durable-nonces](solana/solana-durable-nonces) | Solana | Count Solana transactions that use durable nonces |

The Solana indexers are listed under HyperIndex indexers below.

### HyperIndex indexers

These run as live indexers with a GraphQL API. You can deploy them on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

| Indexer | Chain | How to |
| --- | --- | --- |
| [solana-dex-swaps-by-program](indexers/solana-dex-swaps-by-program) | Solana | Index every swap on Solana's main DEX programs, direct and routed |
| [solana-subscriptions](indexers/solana-subscriptions) | Solana | Index every plan, subscription and pull on Solana's Subscriptions program |
| [privacy-rings-solana](indexers/privacy-rings-solana) | Solana | Index Privacy Rings deposits, withdrawals and private transfers on Solana |
| [metamask-money-account](metamask-money-account) | Monad | Index every MetaMask Money Account deposit, withdrawal and balance |
| [elysium-uniswap-v4-pools](elysium-uniswap-v4-pools) | Elysium | Index every Uniswap v4 pool on Elysium over RPC |
| [elysium-hype-deposits](elysium-hype-deposits) | HyperEVM | Index every HYPE deposit into Elysium through its bridge |

## Use these examples with an AI agent

Each example's README ends with a prompt written for that example. If you want something new, open the repo in Claude Code, Cursor or whatever agent you use and paste this:

```text
Read README.md and two examples in this repo that are close to what I want, for
example usdc-supply-ethereum and aave-v4-avalanche. Then read the HyperSync docs
at https://docs.envio.dev/llms.txt.

Write a new example in its own folder that answers: <YOUR QUESTION>, on <CHAIN>.
Use the HyperSync endpoint for that chain from
https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks, the Python
standard library only, and read my token from the ENVIO_API_TOKEN environment
variable. Run it on a short window first, print the result, then add a README
in the same format as the other examples.
```

Agents read docs better as plain text, so point yours at [docs.envio.dev/llms.txt](https://docs.envio.dev/llms.txt) or the longer [llms-full.txt](https://docs.envio.dev/llms-full.txt).

## FAQ

**What is HyperSync?**
It's Envio's blockchain data API. You ask for logs, transactions or blocks, it filters them on the server and sends back only the fields you want, so reading a chain's full history takes minutes rather than days. The [overview](https://docs.envio.dev/docs/HyperSync/overview) has the details.

**How do I get every ERC-20 transfer for a token?**
Ask HyperSync for the token's `Transfer` logs from block 0 and keep going with `next_block` until you're caught up. [usdc-supply-ethereum](stablecoins-and-payments/usdc-supply-ethereum) and [rlusd-ethereum-supply](stablecoins-and-payments/rlusd-ethereum-supply) both do exactly this and turn the transfers into supply.

**Can I use this instead of eth_getLogs?**
Yes. HyperSync hands back logs for huge block ranges in one request. And if your code already talks JSON-RPC, [HyperRPC](https://docs.envio.dev/docs/HyperRPC/overview-hyperrpc) serves `eth_getLogs` and the other read methods from the same data, so you don't have to change anything.

**Does it work on Solana?**
Yes. The Solana examples read instructions and token balance changes from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana).

**Which chains are supported?**
The full list is [here](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks). Moving most examples to another chain is a one-line change.

**Do I need an SDK?**
No, the scripts just make HTTP requests. For bigger pipelines there are [clients](https://docs.envio.dev/docs/HyperSync/hypersync-clients) for Python, Rust and Node.js.

**When should I use HyperIndex instead?**
A script is great when you want an answer or a one-off backfill. Reach for [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) when you need the data kept up to date and served over GraphQL.

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [HyperRPC](https://docs.envio.dev/docs/HyperRPC/overview-hyperrpc)
- [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) and [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Get an API token](https://envio.dev/app/api-tokens)
- [Envio Discord](https://discord.gg/envio)

MIT licensed. Got an idea for an example, or stuck on one? Come say hi in the [Envio Discord](https://discord.gg/envio).
