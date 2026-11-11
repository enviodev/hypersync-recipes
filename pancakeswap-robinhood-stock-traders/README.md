# PancakeSwap stock token traders on Robinhood

Reads every PancakeSwap v3 and Infinity swap on Robinhood with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It counts the wallets that have swapped since PancakeSwap opened on Robinhood in July, then counts how many of them traded a Robinhood Stock Token and which stock tokens they traded most.

These are the numbers behind Envio's post on PancakeSwap's stock token traders on Robinhood.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It reads every swap since July in 48 block ranges, 16 at a time, and takes about seven minutes.

## What it prints

```
PancakeSwap on Robinhood, blocks up to 111,812,059, first swap 2026-07-01
912,495 swaps in 899,735 transactions from 68,685 wallets
15,653 wallets (22.8%) traded a Robinhood Stock Token in 182,341 transactions
Most traded stock tokens by wallets:
  NVDA     8,167 wallets
  QQQ      6,305 wallets
  AAPL     2,085 wallets
  SPCX       810 wallets
  SPY         89 wallets
```

That run was on 11th Nov 2026, at about 16:00 UTC.

## How it counts

- The PancakeSwap v3 factory `0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865` and Infinity CLPoolManager `0xeE04c68742e6Bf434bE8039580D2e89BBE55bc6f` on Robinhood come from PancakeSwap's [v3](https://developer.pancakeswap.finance/contracts/v3/addresses) and [Infinity](https://developer.pancakeswap.finance/contracts/infinity/resources/addresses) address pages.
- Pools come from the factory's `PoolCreated` events (v3) and the CLPoolManager's `Initialize` events (Infinity), which carry each pool's two tokens.
- Swaps are the v3 pools' `Swap` events and the CLPoolManager's `Swap` events. HyperSync's default join returns each swap with its block and transaction. Only logs whose address and topic0 match a PancakeSwap pool and the swap event are kept.
- A wallet is the address that sent the swap transaction.
- The 203 Robinhood Stock Tokens come from Robinhood's asset API, `GET https://api.robinhood.com/rhj/assets`, documented on the [Stock Token APIs page](https://docs.robinhood.com/chain/stock-token-apis/). A swap counts as a stock token trade when its pool holds a stock token on either side.
- A few automated wallets send a large share of transactions, so the post counts wallets, not transactions.
- Checked against Robinhood's public RPC: `eth_getLogs` on six sample block windows returned the same 166 swap logs as HyperSync, and 25 random transactions had the same sender over `eth_getTransactionByHash`.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Robinhood (chain 4663,
endpoint https://robinhood.hypersync.xyz) to read every PancakeSwap v3 Swap (pools from factory
0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865) and Infinity CL Swap (CLPoolManager
0xeE04c68742e6Bf434bE8039580D2e89BBE55bc6f). My API token is in the ENVIO_API_TOKEN environment
variable. Count unique transaction senders, and how many traded a pool holding a Robinhood Stock
Token from https://api.robinhood.com/rhj/assets.
```

## Learn more

- [HyperSync docs](https://docs.envio.dev/docs/HyperSync/overview)
- [Robinhood on Envio](https://envio.dev/chains/robinhood)
