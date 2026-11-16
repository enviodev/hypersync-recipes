# Arbitrum priority fees

Reads every Arbitrum One transaction since priority fees were switched on and counts the ones that paid a tip to be ordered first, day by day, with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

## What we found

From 23 Sep 2026, when the first priority fee was paid (17:00 UTC), to the end of 15 Nov 2026:

- 39,382,591 transactions paid a priority fee, out of 87,539,107 on the chain
- In the week of 9 to 15 Nov that was 51% of all transactions, up from 38% in the first full week
- Those fees add up to 181.95 ETH, about $447K at each day's ETH price
- The busiest day was 28 Oct, with 1,672,169 transactions paying a priority fee
- The running total passed 35M on 10 Nov, the figure [Arbitrum shared](https://x.com/arbitrum/status/2122052836171071756) along with $400K+ in revenue. Our total to 9 Nov is 34.6M transactions and $410K

## Why it matters

Since [ArbOS 61](https://docs.arbitrum.io/run-arbitrum-node/arbos-releases/arbos61), Arbitrum One orders transactions by priority fee, so a tip on a normal transaction is how an app pays to go first. The fee isn't an event, so you can't get it from logs. You need each transaction's effective gas price and its block's base fee, for every transaction on the chain. HyperSync returns exactly those columns for a block range in one request, which makes a scan of about 100M transactions practical without running a node.

## What it pulls

| | |
|---|---|
| Chain | Arbitrum One, `https://arbitrum.hypersync.xyz` |
| Transactions | `block_number`, `gas_used`, `effective_gas_price` for every transaction |
| Blocks | `number`, `timestamp`, `base_fee_per_gas` |
| Rule | A transaction paid a priority fee when `effective_gas_price` is above its block's `base_fee_per_gas`. The fee is the difference times `gas_used` |
| Window | Block 507,945,268 (start of 23 Sep 2026 UTC) to the chain head |

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). There are no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
FROM_BLOCK=524000000 TO_BLOCK=524300000 python script.py     # a smaller range to try it
```

The full scan splits the range into 50K-block chunks across worker processes (`WORKERS`, default 12) and takes a while. It prints one row per UTC day and writes `arbitrum_priority_fees.json`.

## Check the numbers yourself

- **Against an RPC:** for any block, call `eth_getBlockByNumber` for `baseFeePerGas` and `eth_getBlockReceipts` for each `effectiveGasPrice` and `gasUsed`. For blocks 524,000,000 to 524,000,299 both the public Arbitrum RPC and this script give 1,412 transactions, 797 with a priority fee, and 1,838,517,634,556,150 wei in fees.
- **Against Arbitrum's figures:** the running total column passes 35M on 10 Nov, and fees to 9 Nov come to about $410K.
- **Before the switch:** 20 to 22 Sep show zero transactions above the base fee, which is what you'd expect before priority fees were collected.

Dollar figures use the daily ETH price from [DefiLlama's coins API](https://api-docs.defillama.com/). The script itself reports ETH.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview, endpoint https://arbitrum.hypersync.xyz/query)
to read every Arbitrum One transaction from block 507945268 to the head. Select transaction fields
block_number, gas_used, effective_gas_price and block fields number, timestamp, base_fee_per_gas, with
include_all_blocks true. Page with next_block and retry on HTTP 429. My API token is in ENVIO_API_TOKEN.
A transaction paid a priority fee when effective_gas_price > base_fee_per_gas; the fee is the difference
times gas_used. Print transactions, priority-fee transactions and fees in ETH per UTC day. Then group the
priority fees by the transaction's `to` address to see which contracts pay the most.
```

To keep this running as a live index instead of a one-off scan, scaffold a HyperIndex project with `pnpx envio init`. It adds Envio's agent skills to the project's `.claude/skills/` folder, so your agent has the docs in context ([Quickstart with AI](https://docs.envio.dev/docs/HyperIndex/quickstart-with-ai)).

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview) and [supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [HyperIndex on Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [ArbOS 61 release notes](https://docs.arbitrum.io/run-arbitrum-node/arbos-releases/arbos61) and the [upgrade notice](https://docs.arbitrum.io/notices/arbos61-upgrade-notice)
- [Arbitrum docs on priority fees](https://docs.arbitrum.io/launch-arbitrum-chain/chain-config/costs/priority-fees)
- Questions: [Envio Discord](https://discord.gg/envio)
