# Aero on Robinhood and Ethereum, day by day

Finds every pool created by Aero's factories on Robinhood and on Ethereum, reads every swap in them since launch with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), prices each swap in dollars and prints volume, swaps and wallets per day for the two chains side by side.

These are the numbers behind Envio's post on Aero's first 25 days on Robinhood and Ethereum.

## The finding

Aero's first swaps on Robinhood and on Ethereum both happened on 21 Oct 2026. Over the 25 full UTC days from 22 Oct to 15 Nov 2026:

| | Robinhood | Ethereum |
| --- | --- | --- |
| Swap volume | $1,696.5M | $2,016.4M |
| Swaps | 1,692,885 | 249,107 |
| Average swap | $1,002 | $8,094 |
| Pools | 114 | 124 |

- Robinhood did 84% of Ethereum's volume with 6.8 times as many swaps.
- Robinhood traded more than Ethereum on 7 of the 25 days.
- In the last 7 days (9 to 15 Nov) Robinhood did $563.2M across 656,476 swaps and Ethereum did $667.4M across 81,191.

## Why it matters

The same DEX went live on two chains on the same day, so the two are easy to compare. Volume alone says they're close. The swap count says the trading is very different: lots of everyday-size trades on Robinhood, fewer and bigger ones on Ethereum. If you're building on either chain, that tells you what kind of flow to expect, and you only see it when you read every swap instead of a daily total.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

That covers every full UTC day so far. Pass a date to stop after that day. The post used:

```bash
python3 script.py 2026-11-15
```

The Robinhood pull reads about 22M blocks and 1.7M swaps, so give it around 15 minutes.

## What it prints

```
Aero on Robinhood: 114 pools, first swap 2026-10-21, $1,696.5M across 1,693,153 swaps from 31,059 wallets (10 unpriced)
Aero on Ethereum: 124 pools, first swap 2026-10-21, $2,016.4M across 249,232 swaps from 16,003 wallets (140 unpriced)

day          Robinhood     Ethereum   Robinhood as % of Ethereum
2026-10-22  $    24.0M  $    10.7M   225.2%
2026-10-23  $    38.1M  $    21.1M   181.1%
2026-10-24  $    35.3M  $    15.9M   221.5%
...
2026-11-13  $    88.2M  $    91.4M    96.5%
2026-11-14  $    91.1M  $   108.2M    84.2%
2026-11-15  $    83.3M  $    89.8M    92.8%

Robinhood, 2026-11-09 to 2026-11-15: $563.2M, 656,476 swaps, 10,852 wallets, $858 a swap

Ethereum, 2026-11-09 to 2026-11-15: $667.4M, 81,191 swaps, 6,882 wallets, $8,220 a swap
```

The first two lines include the few swaps on 21 Oct, the day the pools opened.

## How it counts

- Factories come from Aero's [deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses) (`cl-robinhood.json`, `pools-robinhood.json`, `cl-ethereum.json` and `pools-ethereum.json`): the CL pool factory, the volatile pool factory and the stable pool factory. Robinhood has other factories that emit the same `PoolCreated` event, so only these three addresses are used. Their `allPoolsLength()` onchain matches the pools found here.
- Volume is each swap valued on one side. A dollar stablecoin side counts at $1 (USDG on Robinhood, and USDC, USDT, DAI, crvUSD, frxUSD, USDe and USDS on Ethereum). Otherwise WETH or BTC is used, priced from Aero's own stablecoin pools at the time of the swap, and then any other token priced from its Aero pool. A few swaps with no dollar route are left unpriced.
- Wallets are the distinct senders of transactions that contain a swap, so routers and bots count too.
- Days are UTC.

## Check the numbers yourself

DefiLlama tracks the same pools. Its daily Aero Slipstream volume for Robinhood and Ethereum is in the `totalDataChartBreakdown` field of https://api.llama.fi/summary/dexs/aero-slipstream. Over 22 Oct to 15 Nov 2026 it sums to $1,694.3M on Robinhood and $2,017.2M on Ethereum. This script is within 0.2% of both totals and within about 1% on every single day.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every swap in
Aero's pools on Robinhood and Ethereum. Start from script.py in
https://github.com/enviodev/hypersync-recipes/tree/main/aero-robinhood-ethereum. The pool
factories are listed in
https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses
(cl-<chain>.json and pools-<chain>.json). My API token is in the ENVIO_API_TOKEN environment
variable. Add Base, Arbitrum and Optimism from the same folder, then chart daily swap volume
and average swap size per chain. Check one day per chain against
https://api.llama.fi/summary/dexs/aero-slipstream before you trust the totals.
```

## Sources

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview) and [supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aero](https://aero.xyz) and its [deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/tree/main/deployment-addresses)
- [Robinhood's chain docs](https://docs.robinhood.com/chain/)
- [DefiLlama, Aero Slipstream](https://defillama.com/protocol/aero-slipstream)
- [Envio Discord](https://discord.gg/envio)
