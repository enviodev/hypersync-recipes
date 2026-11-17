# ether.fi card payments on Optimism

From 9 to 15 Nov 2026 (UTC), on OP Mainnet, **36K ether.fi cardholders made 457K card payments worth $33.5M, and the typical cardholder's payment was $13.45**.

- $13.45 is the median, across cardholders, of each cardholder's own median payment, so a few very busy accounts can't move it.
- More than 5.5K cardholders paid with the card on every day of the week.
- 90.3% of payments were under $100, and the median single payment was $9.92.

## Why it's interesting

ether.fi Cash settles every card payment onchain, so one event gives you real-world card spending, payment by payment. That's rare. If you're building a crypto card, a spending dashboard or a rewards program, this shows what everyday card use looks like onchain, mostly small and frequent payments, and how to measure it for your own users.

## What it pulls

`Spend` logs from ether.fi's `CashEventEmitter` on OP Mainnet, joined to each block's timestamp.

- `CashModule` [`0x7Ca0b75E67E33c0014325B739A8d019C4FE445F0`](https://optimistic.etherscan.io/address/0x7Ca0b75E67E33c0014325B739A8d019C4FE445F0) calls `CashEventEmitter` [`0x380B2e96799405be6e3D965f4044099891881acB`](https://optimistic.etherscan.io/address/0x380B2e96799405be6e3D965f4044099891881acB) on every payment. Both are on ether.fi's [deployed contracts](https://etherfi.gitbook.io/etherfi/contracts-and-integrations/deployed-contracts) page and in the [cash-v3 repo](https://github.com/etherfi-protocol/cash-v3/tree/master/deployments/mainnet).
- The event is `Spend(address indexed safe, bytes32 indexed txId, BinSponsor indexed binSponsor, address[] tokens, uint256[] amounts, uint256[] amountInUsd, uint256 totalUsdAmt, Mode mode)` from [`CashEventEmitter.sol`](https://github.com/etherfi-protocol/cash-v3/blob/master/src/modules/cash/CashEventEmitter.sol). `totalUsdAmt` has 6 decimals.

How it counts.

- Each `txId` is counted once. The query uses HyperSync's default join, so the script keeps only logs whose address and topic0 match.
- Card payments are the `Reap` and `Rain` issuers from the `BinSponsor` enum in [`ICashModule.sol`](https://github.com/etherfi-protocol/cash-v3/blob/master/src/interfaces/ICashModule.sol). `PIX` (Brazil's Pix rail) and `CardOrder` are printed in the issuer breakdown but left out of card payments.
- A cardholder is one ether.fi safe, the `safe` topic on the event.
- The dollar amounts are the event's own `totalUsdAmt`, so there's no outside price feed.

Every number comes from HyperSync.

## Run it

You need Python 3.9 or newer and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                          # the last 7 full UTC days
python3 script.py 2026-11-09 2026-11-15    # the window used above, both dates included
```

A week is about 460K events and takes a few minutes. Sample output for 9 to 15 Nov 2026.

```
ether.fi Cash on Optimism, 09 Nov to 15 Nov 2026 UTC (7 days)
Spend events by issuer: {'Rain': 443720, 'PIX': 3879, 'Reap': 13565, 'CardOrder': 917}
Spend events by mode:   {'Debit': 438250, 'Credit': 23831}

Card payments 457,285  USD $33,481,254  cardholders 36,072
Median payment $9.92  under $100 90.3%
Typical payment per cardholder (median of each cardholder's own median) $13.45
Cardholders whose typical payment is under $20: 63.3%
Cardholders who paid on all 7 days: 5,547

day         payments  cardholders  usd
2026-11-09    64,048       18,447  $   4,834,198
2026-11-10    61,701       18,653  $   5,742,068
2026-11-11    62,917       18,668  $   4,806,000
2026-11-12    70,053       18,745  $   5,344,265
2026-11-13    65,462       18,849  $   4,537,266
2026-11-14    71,537       19,327  $   4,550,177
2026-11-15    61,567       17,764  $   3,667,280
```

## Change the window

Pass a start and an end date. The script works out a start block from the chain head at 43,200 blocks a day (one every 2 seconds), splits the range across 4 threads, and keeps only events whose block timestamp falls in the window. For a month or more, raise `THREADS` if you hit timeouts. ether.fi Cash runs on OP Mainnet, so the chain stays the same, but the same pattern works for any card program that logs its payments onchain. The [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) has every HyperSync endpoint.

## Check the numbers

- **Over RPC, as the comparison.** `eth_getLogs` on `https://mainnet.optimism.io` for the emitter and the `Spend` topic over one hour (blocks 159,613,747 to 159,615,547) returned 3,885 events and $291,946.88, the same as HyperSync for that range.
- **From transactions.** In the 24 hours to 16 Nov 2026 13:40 UTC, HyperSync saw 62,904 calls to `spend()` on the `CashModule` and 62,909 `Spend` events.
- **Single payments.** Open any transaction on [Optimistic Etherscan](https://optimistic.etherscan.io) and compare the decoded `Spend` event with the script.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Optimism to read every
Spend event from ether.fi's CashEventEmitter
0x380B2e96799405be6e3D965f4044099891881acB and turns it into card payments,
cardholders and USD per day. topic1 is the cardholder's safe, topic2 the
payment id, topic3 the card issuer (0 Reap, 1 Rain, 2 PIX, 3 CardOrder), and
the 4th 32-byte word of data is the USD amount with 6 decimals. My HyperSync
token is in the ENVIO_API_TOKEN environment variable.

Add a breakdown of card payments by hour of day (UTC) and by payment size
bucket (under $10, $10 to $100, $100 to $1,000, over $1,000). Keep the
standard library only. Run it for one day first and check that the bucket
counts add up to the day's card payments.
```

To keep it live instead of re-running a script, ask the agent to turn it into a [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer on the same event and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service).

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [ether.fi Cash contracts](https://etherfi.gitbook.io/etherfi/contracts-and-integrations/deployed-contracts) and the [cash-v3 source](https://github.com/etherfi-protocol/cash-v3)
- [OP Mainnet docs](https://docs.optimism.io)
- [Envio Discord](https://discord.gg/envio)
