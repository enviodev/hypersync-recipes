# Uniswap v4 hooks on Ethereum

As of 17 Nov 2026, **202K Uniswap v4 pools have been created on Ethereum and 48.7K of them (24.0%) use a hook**, across 11.4K different hook contracts. October 2026 was the biggest month so far, with 34.1K new pools and 10.4K of them on a hook.

| Month | Pools | With a hook |
| --- | --- | --- |
| 2026-08 | 14,121 | 3,670 |
| 2026-09 | 20,159 | 5,334 |
| 2026-10 | 34,072 | 10,412 |
| 2026-11 (to 17 Nov) | 19,610 | 2,129 |
| All time | 202,419 | 48,679 |

## Why it's interesting

Hooks are what's new in Uniswap v4. A hook is a contract that runs custom logic around a pool's swaps and liquidity, and every pool names its hook once, in the `Initialize` event. So one event on one contract tells you every pool ever created, which hooks they use and how that's changing month by month. It's one of the simplest HyperSync queries there is.

## What it pulls

- Every `Initialize` log on the v4 PoolManager on Ethereum, `0x000000000004444c5dc75cB358380D2e3dE08A90` ([Uniswap's v4 deployments](https://docs.uniswap.org/contracts/v4/deployments)), from block 21,688,329 when it was deployed.
- Block timestamps, to put each pool in a UTC month.

The hook is the third word of the event's data, after `fee` and `tickSpacing`. A pool uses a hook when that address isn't the zero address. All the numbers come from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py
```

It reads every pool up to the latest block and takes about two and a half minutes. Sample output from a run on 17 Nov 2026.

```
202,419 v4 pools on Ethereum, 48,679 with a hook (24.0%), 11,441 different hook contracts

2025-01      201 pools       13 with a hook
2025-02    1,376 pools       50 with a hook
...
2026-09   20,159 pools    5,334 with a hook
2026-10   34,072 pools   10,412 with a hook
2026-11   19,610 pools    2,129 with a hook

Most used hooks:
  0x322dcec4958c14e021a9f1cd49df11b9457968cc  6,528 pools
  0x0d62529346ac2c61f5c0582210d01214687bc0cc  5,116 pools
  0x96b893683afbfec071e90f78d00de4bb932fe0cc  2,240 pools
  0x07f17023db9cec3f8c6bb53c6940e29dffb0a0cc  1,290 pools
  0x6c24d0bcc264ef6a740754a11ca579b9d225e8cc  1,285 pools
```

The current month is partial, and new pools are created every day, so your numbers will be higher.

## Change the window or chain

- **Window.** The script always starts at `START_BLOCK`. To stop at a fixed block, add `"to_block": <block>` to the query body and stop the loop when `next_block` reaches it. The [uniswap-v4-hooks-robinhood](../uniswap-v4-hooks-robinhood) example already takes an end block, and `--ethereum` runs it on Ethereum.
- **Chain.** v4 is live on many chains. Swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), and `POOL_MANAGER` and `START_BLOCK` for that chain's PoolManager from [Uniswap's v4 deployments](https://docs.uniswap.org/contracts/v4/deployments).

## Check the numbers

The monthly pool counts add up to the total. To check one pool, open any `Initialize` event on the [PoolManager on Etherscan](https://etherscan.io/address/0x000000000004444c5dc75cB358380D2e3dE08A90#events) and compare its `hooks` field with what the script decodes.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Initialize event
on the Uniswap v4 PoolManager on Ethereum and counts pools with and without a
hook, month by month. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Also read every Swap event on the PoolManager (topic1 is the pool ID) and add a
swap count per hook, so the top hooks are ranked by swaps as well as pools. Keep
the standard library only. Run it for the last 7 days of swaps first and check
that the swaps per hook add up to the total swaps in that window.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Uniswap v4 deployments](https://docs.uniswap.org/contracts/v4/deployments)
- [Uniswap v4 multichain indexer with HyperIndex](https://docs.envio.dev/docs/HyperIndex/example-uniswap-v4-multi-chain-indexer)
- [Envio Discord](https://discord.gg/envio)
