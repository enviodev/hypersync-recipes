# PancakeSwap's stock token traders on Robinhood Chain

From PancakeSwap's first swap on Robinhood Chain on 1 Jul 2026 to 11 Nov 2026, **68.7K wallets made 914K swaps, and 15.7K of them (22.8%) traded a Robinhood Stock Token**. NVDA was the most traded by wallet count at 8.2K wallets, then QQQ at 6.3K. 61.5% of stock token traders only ever traded while US markets were closed.

| Stock token | Wallets |
| --- | --- |
| NVDA | 8,186 |
| QQQ | 6,305 |
| AAPL | 2,085 |
| SPCX | 811 |
| SPY | 89 |

## Why it's interesting

Stock tokens on Robinhood Chain trade on more than one DEX, and each brings its own crowd. This shows how many of PancakeSwap's traders on the chain have picked up stock tokens and when they trade them. It also covers two pool designs in one script, classic v3 pools from a factory and Infinity's singleton pool manager, which is handy if you track any DEX that runs both.

## What it pulls

- PancakeSwap v3 pools from the factory's `PoolCreated` events and Infinity pools from the CLPoolManager's `Initialize` events. The v3 factory is [`0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865`](https://developer.pancakeswap.finance/contracts/v3/addresses) and the Infinity CLPoolManager is [`0xeE04c68742e6Bf434bE8039580D2e89BBE55bc6f`](https://developer.pancakeswap.finance/contracts/infinity/resources/addresses).
- Every `Swap` in the v3 pools and on the CLPoolManager, each with its block and transaction, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Every number here comes from HyperSync.
- The 203 Robinhood Stock Tokens from Robinhood's asset API, `GET https://api.robinhood.com/rhj/assets`, documented on the [Stock Token APIs page](https://docs.robinhood.com/chain/stock-token-apis/).

A wallet is the address that sent the swap transaction. A swap is a stock token trade when its pool holds a stock token on either side. US market hours are 9:30 to 16:00 New York time on weekdays. Nights, weekends and the two NYSE holidays in the window (3 Jul and 7 Sep 2026) count as closed. A few automated wallets send a large share of transactions, so the stock token figures count wallets rather than transactions.

## Run it

You need Python 3.9 or newer (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It reads every swap since July in 48 block ranges, 16 at a time, and takes about seven minutes. Sample output from a run on 11 Nov 2026 at about 17:50 UTC:

```
PancakeSwap on Robinhood, blocks up to the chain head, first swap 2026-07-01
914,111 swaps in 901,344 transactions from 68,726 wallets
15,673 wallets (22.8%) traded a Robinhood Stock Token in 183,369 transactions
Most traded stock tokens by wallets:
  NVDA     8,186 wallets
  QQQ      6,305 wallets
  AAPL     2,085 wallets
  SPCX       811 wallets
  SPY         89 wallets
When stock token wallets traded (New York time):
  only while US markets were closed   9,634 (61.5%)
  both                                2,378 (15.2%)
  only during market hours            3,661 (23.4%)
```

## Change the window or chain

- **Window.** The script reads from PancakeSwap's first block on Robinhood Chain to the head. Raise the start block to look at a recent stretch only, and it'll run faster.
- **Chain.** PancakeSwap v3 and Infinity run on other chains too. Swap `URL` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and the factory and CLPoolManager for that chain's addresses from PancakeSwap's address pages. Replace the stock token list with whatever set of tokens you want to track there.

## Check the numbers

The HyperSync results were checked against Robinhood Chain's public RPC as the comparison. `eth_getLogs` on six sample block windows returned the same 166 swap logs as HyperSync, and 25 random transactions had the same sender over `eth_getTransactionByHash`.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent:

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) on Robinhood Chain to read every
PancakeSwap v3 and Infinity swap and count the wallets that traded a Robinhood Stock
Token. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a weekly table of new stock token wallets, counting each wallet in the week of its
first stock token swap, and write it to new_wallets_weekly.csv. Keep the standard
library only. Then check that the weekly new wallets add up to the 15,673 total the
script prints, or to whatever total your run prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Robinhood Chain on Envio](https://envio.dev/chains/robinhood)
- [PancakeSwap v3 addresses](https://developer.pancakeswap.finance/contracts/v3/addresses)
- [PancakeSwap Infinity addresses](https://developer.pancakeswap.finance/contracts/infinity/resources/addresses)
- [Robinhood Stock Token APIs](https://docs.robinhood.com/chain/stock-token-apis/)
- [Envio Discord](https://discord.gg/envio)
