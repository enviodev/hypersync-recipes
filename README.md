# HyperSync recipes: example scripts for onchain data

Curated, ready-to-run example scripts that pull real onchain data with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), Envio's blockchain data API. Each recipe answers one concrete question, such as how much USDC was minted on Ethereum this week, who holds a tokenized stock, or how much is supplied to an Aave market, and prints the answer in your terminal.

Use them as working starting points. Copy a recipe, change the contract, chain or time window, and you have your own analytics, backfill or data pipeline. Every recipe comes with a prompt you can paste into Claude Code, Cursor or any coding agent to adapt it for you.

- **74 recipes** across Ethereum, Base, Arbitrum, Optimism, Polygon, BNB Chain, Avalanche, Monad, Gnosis, Ink, Arc, Robinhood Chain, HyperEVM, Tempo and Solana.
- **Python standard library only** for the HyperSync scripts. No SDK to install, no node to run.
- **HyperIndex indexers** for the recipes that need a live GraphQL API.

## Quick start

1. Get a free API token at [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).
2. Clone the repo and run a recipe.

```bash
git clone https://github.com/enviodev/hypersync-recipes.git
cd hypersync-recipes/usdc-supply-ethereum
export ENVIO_API_TOKEN=your-token
python3 script.py
```

Each folder's README explains the finding, what the script pulls, how to change the window or chain, how to check the numbers and the agent prompt for that recipe.

## Recipes

### Stablecoins and payments

| Recipe | Chain | How to |
| --- | --- | --- |
| [usdc-supply-ethereum](usdc-supply-ethereum) | Ethereum | Pull every USDC mint and burn on Ethereum and track supply day by day |
| [rlusd-ethereum-supply](rlusd-ethereum-supply) | Ethereum | Rebuild Ripple USD (RLUSD) supply from every mint and burn |
| [arc-usdc-mint-burn](arc-usdc-mint-burn) | Arc | Pull every USDC mint and burn on Arc, including Circle Gateway and CCTP |
| [arc-stablecoins-30d](arc-stablecoins-30d) | Arc | Track USDC and EURC supply on Arc over 30 days |
| [monad-stablecoin-weekends](monad-stablecoin-weekends) | Monad | Pull every stablecoin transfer on Monad and compare weekdays with weekends |
| [ousd-supply-by-chain](ousd-supply-by-chain) | Ethereum, Base, Tempo | Track Open USD (OUSD) supply and holders on each chain |
| [base-usdc-micropayments](base-usdc-micropayments) | Base | Pull every gasless USDC payment on Base and size it down to the cent |
| [uniswap-stable-volume-by-chain](uniswap-stable-volume-by-chain) | 22 EVM chains | Get Uniswap stablecoin-to-stablecoin volume on 22 chains |
| [etherfi-cash-card-payments](etherfi-cash-card-payments) | Optimism | Pull every ether.fi Cash card payment settled onchain |
| [phantom-cash-supply](phantom-cash-supply) | Solana | Track Phantom CASH stablecoin supply week by week |
| [sofiusd-solana](sofiusd-solana) | Solana | Rebuild SoFiUSD supply on Solana from every mint and burn |
| [huma-payfi-solana](huma-payfi-solana) | Solana | Pull every Huma Institutional drawdown and repayment on Solana |

### Tokenized stocks

| Recipe | Chain | How to |
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
| [jupiter-lend-stock-collateral](jupiter-lend-stock-collateral) | Solana | Pull every Jupiter Lend borrow position, grouped by collateral |
| [backpack-stocks-solana](backpack-stocks-solana) | Solana | Track Backpack tokenized stock holders, mints and burns on Solana |

### Tokenized funds and real-world assets

| Recipe | Chain | How to |
| --- | --- | --- |
| [blackrock-buidl-by-chain](blackrock-buidl-by-chain) | EVM chains | Track BlackRock BUIDL supply on each chain from every mint and burn |
| [tokenized-treasuries-solana](tokenized-treasuries-solana) | Solana | Track the supply of tokenized Treasury funds on Solana, day by day |
| [ondo-intelligent-portfolios](ondo-intelligent-portfolios) | Ethereum, BNB Chain | Track Ondo Intelligent Portfolios supply and holders |
| [spiko-safo](spiko-safo) | Ethereum, Arbitrum, Polygon, Base | Track Spiko SAFO supply and holders by chain and share class |
| [grove-basin-jtrsy](grove-basin-jtrsy) | Ethereum | Pull every Grove Basin swap of JTRSY into USDC |
| [kamino-rwa-collateral](kamino-rwa-collateral) | Solana | Find real-world credit used as collateral on Kamino Lend |
| [pendle-strcx](pendle-strcx) | Ethereum | Find every STRCx holder and how much sits in Pendle |
| [paxg-on-morpho-base](paxg-on-morpho-base) | Base | Track USDC borrowed against Paxos Gold (PAXG) on Morpho |

### Lending and vaults

| Recipe | Chain | How to |
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
| [safenet-staking](safenet-staking) | Ethereum | Track SAFE staked in Safenet and active stakers week by week |

### DEXs, perps and prediction markets

| Recipe | Chain | How to |
| --- | --- | --- |
| [uniswap-robinhood-chain](uniswap-robinhood-chain) | Robinhood Chain | Pull every Uniswap v2, v3 and v4 swap on Robinhood Chain |
| [uniswap-volatilepair-robinhood](uniswap-volatilepair-robinhood) | Robinhood Chain | Get swaps, volume and LP fees for one Uniswap pool |
| [uniswap-v4-hooks-ethereum](uniswap-v4-hooks-ethereum) | Ethereum | Find every Uniswap v4 pool with a hook on Ethereum |
| [uniswap-v4-hooks-robinhood](uniswap-v4-hooks-robinhood) | Robinhood Chain | Find every Uniswap v4 pool and swap by hook |
| [aero-pools-arbitrum](aero-pools-arbitrum) | Arbitrum | Rank every Aero pool on Arbitrum by volume and liquidity |
| [aero-robinhood-ethereum](aero-robinhood-ethereum) | Robinhood Chain, Ethereum | Track Aero DEX volume day by day on two chains |
| [yieldbasis-weth-propamm](yieldbasis-weth-propamm) | Ethereum | Compare Yield Basis pool volume and fees before and after oracle pricing |
| [metric-first-month-ethereum](metric-first-month-ethereum) | Ethereum | Pull every swap on Metric's pools, per day |
| [ostium-markets-arbitrum](ostium-markets-arbitrum) | Arbitrum | Pull every Ostium position and group it by market |
| [phoenix-perps-signups](phoenix-perps-signups) | Solana | Track Phoenix trading accounts and USDC deposits on Solana |
| [polymarket-election-day](polymarket-election-day) | Polygon | Get Polymarket trading volume by hour on US election day |
| [polymarket-election-night](polymarket-election-night) | Polygon | Get Polymarket trading volume hour by hour on US election night |
| [metadao-launchpad-raises](metadao-launchpad-raises) | Solana | Pull every MetaDAO launchpad raise on Solana |

### Chain activity, wallets and accounts

| Recipe | Chain | How to |
| --- | --- | --- |
| [active-addresses-without-dusting](active-addresses-without-dusting) | EVM chains | Count daily active addresses with dusting filtered out |
| [monad-biggest-apps](monad-biggest-apps) | Monad | Rank Monad apps by transactions over 30 days |
| [monad-volatility-day](monad-volatility-day) | Monad | Compare one day on Monad with a 30-day baseline, hour by hour |
| [gnosis-biggest-protocols](gnosis-biggest-protocols) | Gnosis | Rank the busiest protocols on Gnosis Chain |
| [ink-monthly-activity](ink-monthly-activity) | Ink | Count Ink transactions and active addresses by month |
| [polygon-october-fees](polygon-october-fees) | Polygon | Find which contracts paid the most gas on Polygon PoS |
| [arbitrum-priority-fees](arbitrum-priority-fees) | Arbitrum | Count Arbitrum transactions paying a priority fee, day by day |
| [erc4337-user-operations-ethereum](erc4337-user-operations-ethereum) | Ethereum | Pull every ERC-4337 user operation on Ethereum |
| [ethereum-approval-cleanups](ethereum-approval-cleanups) | Ethereum | Find every ERC-20 approval revoked on Ethereum |
| [safe-growth](safe-growth) | 14 chains | Count every Safe created, by month and chain |
| [safe-shared-signer](safe-shared-signer) | Ethereum | Decode every new Safe's owners and find the most common signer |
| [circles-trust-gnosis](circles-trust-gnosis) | Gnosis | Count Circles v2 humans and trust links on Gnosis Chain |
| [uni-new-holders](uni-new-holders) | Ethereum | Count new UNI holders per day since 2020 |
| [solana-durable-nonces](solana-durable-nonces) | Solana | Count Solana transactions that use durable nonces |

### HyperIndex indexers

These run as live indexers with a GraphQL API. You can deploy them on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

| Indexer | Chain | How to |
| --- | --- | --- |
| [solana-dex-swaps-by-program](solana-dex-swaps-by-program) | Solana | Index every swap on Solana's main DEX programs, direct and routed |
| [solana-subscriptions](solana-subscriptions) | Solana | Index every plan, subscription and pull on Solana's Subscriptions program |
| [privacy-rings-solana](privacy-rings-solana) | Solana | Index Privacy Rings deposits, withdrawals and private transfers on Solana |
| [metamask-money-account](metamask-money-account) | Monad | Index every MetaMask Money Account deposit, withdrawal and balance |
| [elysium-uniswap-v4-pools](elysium-uniswap-v4-pools) | Elysium | Index every Uniswap v4 pool on Elysium over RPC |
| [elysium-hype-deposits](elysium-hype-deposits) | HyperEVM | Index every HYPE deposit into Elysium through its bridge |

## Use these recipes with an AI agent

Every recipe README ends with a "Build your own with an AI agent" prompt written for that recipe. For anything new, paste this into Claude Code, Cursor or another coding agent from the repo root:

```text
Read README.md and two recipes in this repo that are close to what I want, for
example usdc-supply-ethereum and aave-v4-avalanche. Then read the Envio HyperSync
docs at https://docs.envio.dev/llms.txt.

Write a new recipe in its own folder that answers: <YOUR QUESTION>, on <CHAIN>.
Use the HyperSync endpoint for that chain from
https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks, the Python
standard library only, and read my token from the ENVIO_API_TOKEN environment
variable. Run it on a short window first, print the result, then add a README
in the same format as the other recipes.
```

The full Envio docs are available as plain text for agents at [docs.envio.dev/llms.txt](https://docs.envio.dev/llms.txt) and [docs.envio.dev/llms-full.txt](https://docs.envio.dev/llms-full.txt).

## FAQ

**What is HyperSync?**
HyperSync is Envio's blockchain data API. It lets you query logs, transactions and blocks across dozens of chains, filtered on the server and returned with only the fields you ask for, so you can read a whole chain's history in minutes. Read the [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview).

**How do I get every ERC-20 transfer for a token?**
Query the token's `Transfer` logs from block 0 with HyperSync and page through with `next_block`. [usdc-supply-ethereum](usdc-supply-ethereum) and [rlusd-ethereum-supply](rlusd-ethereum-supply) do this and turn the transfers into supply.

**Can I use this instead of eth_getLogs?**
Yes. HyperSync returns logs for wide block ranges in one request. If your code already speaks JSON-RPC, [HyperRPC](https://docs.envio.dev/docs/HyperRPC/overview-hyperrpc) serves `eth_getLogs` and other read methods from the same data.

**Does it work on Solana?**
Yes. The Solana recipes use the [HyperSync Solana endpoint](https://docs.envio.dev/docs/HyperSync/solana) to read instructions and token balance changes.

**Which chains are supported?**
See the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks). Most recipes switch chain by changing one URL.

**Do I need an SDK?**
No. The scripts use plain HTTP and the Python standard library. Official [clients](https://docs.envio.dev/docs/HyperSync/hypersync-clients) for Python, Rust and Node.js are there for larger pipelines.

**When should I use HyperIndex instead?**
Use a script when you need an answer or a backfill. Use [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) when you need the data kept up to date and served as a GraphQL API.

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [HyperRPC](https://docs.envio.dev/docs/HyperRPC/overview-hyperrpc)
- [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) and [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Get an API token](https://envio.dev/app/api-tokens)
- [Envio Discord](https://discord.gg/envio)

MIT licensed. Contributions and new recipe ideas are welcome in the [Envio Discord](https://discord.gg/envio).
