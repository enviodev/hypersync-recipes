# Arbitrum priority fees, day by day

Arbitrum One started collecting priority fees on 23 Sep 2026, and the first tip landed at 17:00 UTC that day. From then to the end of 15 Nov 2026 (UTC), **39.4M transactions paid a priority fee, out of 87.5M on the chain, and those fees came to 181.95 ETH**.

- In the week of 9 to 15 Nov, 51% of transactions paid a priority fee, up from 38% in the first full week.
- The busiest day was 28 Oct, with 1.67M transactions paying a priority fee.
- The running total passed 35M on 10 Nov, the figure [Arbitrum shared](https://x.com/arbitrum/status/2122052836171071756). Our total to 9 Nov is 34.6M.
- At each day's ETH price the fees came to about $447K, and about $410K up to 9 Nov. Those two dollar figures were priced with a daily ETH price from an outside feed in the original run. The script now prices each day's fees from the Chainlink ETH/USD logs it reads through HyperSync, so a fresh full scan prints its own dollar total.

## Why it's interesting

[ArbOS 61](https://docs.arbitrum.io/run-arbitrum-node/arbos-releases/arbos61) let Arbitrum chains collect priority fees, and Arbitrum One then moved to ordering transactions by [priority fee](https://docs.arbitrum.io/launch-arbitrum-chain/chain-config/costs/priority-fees). So a tip on a normal transaction is now how an app pays to go first.

The fee isn't an event, so logs won't give it to you. You need each transaction's effective gas price and its block's base fee, for every transaction on the chain. HyperSync returns exactly those columns for a whole block range in one request, which makes a scan of about 100M transactions doable without running a node.

## What it pulls

- **Chain.** Arbitrum One, from `https://arbitrum.hypersync.xyz`.
- **Transactions.** `block_number`, `gas_used` and `effective_gas_price` for every transaction.
- **Blocks.** `number`, `timestamp` and `base_fee_per_gas`, with `include_all_blocks` on.
- **Rule.** A transaction paid a priority fee when `effective_gas_price` is above its block's `base_fee_per_gas`. The fee is the difference times `gas_used`.
- **Window.** Block 507,945,268 (the start of 23 Sep 2026 UTC) to the chain head.
- **ETH price.** `AnswerUpdated` logs of the Chainlink ETH/USD aggregator on Arbitrum One (`0xd827123d014578c965f6c9d87a641ec05faa5501`, behind the feed proxy `0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612`), from HyperSync. Each UTC day's fees are priced at that day's average answer, and a day with no update uses the last answer before it.

Every count, the ETH total and the dollar prices come from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
FROM_BLOCK=524000000 TO_BLOCK=524000300 python3 script.py   # 300 blocks, a quick try
python3 script.py                                            # 23 Sep 2026 to the chain head
```

The full scan splits the range into 50K-block chunks across worker processes (`WORKERS`, default 12) and takes a while. It prints progress to stderr, then one row per UTC day with transactions, transactions with a priority fee, their share, fees in ETH and the running total of tipped transactions. It adds the day's ETH/USD price and the fees in dollars to each row. It ends with the totals, including the dollar total, and writes the daily numbers to `arbitrum_priority_fees.json` next to the script.

## Change the window or chain

- **Window.** Set `FROM_BLOCK` and `TO_BLOCK`. `TO_BLOCK` is exclusive, and leaving it out runs to the chain head. Arbiscan's [block by date](https://arbiscan.io/blockdateconverter) tool gives you a start block for any day.
- **Chain.** Any Arbitrum chain on ArbOS 61 or later works the same way. Change the `URL` constant in `script.py` to its HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and set `FROM_BLOCK` to the block where priority fees were switched on there.

## Check the numbers

- **Against an RPC, as the comparison.** For blocks 524,000,000 to 524,000,299, call `eth_getBlockByNumber` for `baseFeePerGas` and `eth_getBlockReceipts` for each `effectiveGasPrice` and `gasUsed` on the public Arbitrum RPC. Both the RPC and the script give 1,412 transactions, 797 with a priority fee and 1,838,517,634,556,150 wei in fees. The quick-try command above runs exactly that range.
- **Against Chainlink over RPC.** A scan that runs to the chain head ends with a labelled check that prints the ETH/USD feed's `latestAnswer` over Arbitrum's public RPC next to the last answer HyperSync read. On 17 Nov 2026 both were $1,807.11. The quick try on the latest 300 blocks printed 925 tipped transactions of 1,963, fees worth $3 at an average $1,818 for the day.
- **Against Arbitrum's figure.** The running total column passes 35M on 10 Nov, the day Arbitrum shared it.
- **Before the switch.** Run with `FROM_BLOCK` set to the start of 20 Sep and `TO_BLOCK=507945268`. 20 to 22 Sep show no transactions above the base fee, which is what you'd expect before priority fees were collected.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Arbitrum One
transaction's gas_used and effective_gas_price, plus each block's
base_fee_per_gas, and counts the transactions that paid a priority fee per UTC
day. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add the transaction's `to` address to the field selection and group the
priority fees by it, so I can see which 20 contracts pay the most in tips.
Keep the standard library only. Run it with FROM_BLOCK=524000000
TO_BLOCK=524000300 first and check that the totals still come to 1,412
transactions, 797 with a priority fee and 1,838,517,634,556,150 wei.
```

To keep this running live instead of as a one-off scan, scaffold a [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) project with `pnpx envio init` and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [ArbOS 61 release notes](https://docs.arbitrum.io/run-arbitrum-node/arbos-releases/arbos61) and the [upgrade notice](https://docs.arbitrum.io/notices/arbos61-upgrade-notice)
- [Arbitrum docs on priority fees](https://docs.arbitrum.io/launch-arbitrum-chain/chain-config/costs/priority-fees)
- [Envio Discord](https://discord.gg/envio)
