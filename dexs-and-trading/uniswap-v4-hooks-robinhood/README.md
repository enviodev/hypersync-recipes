# Uniswap v4 hooks on Robinhood Chain

Up to block 110,095,000, **1.14M Uniswap v4 pools were created on Robinhood Chain and 397K of them (34.9%) use a hook**. Those pools run on 31.8K different hook contracts. Of the 217M v4 swaps, 109M (50.2%) went through a pool with a hook.

| Robinhood Chain | |
| --- | --- |
| Pools created | 1,137,941 |
| With a hook | 397,135 (34.9%) |
| Different hooks | 31,823 |
| Hooks used by 10+ pools | 771 |
| Swaps | 216,981,683 |
| Swaps in pools with a hook | 108,945,756 (50.2%) |

The same script on Ethereum, up to block 26,378,070, finds 193K pools, 47.7K of them (24.7%) with a hook, across 11.3K different hooks.

## Why it's interesting

A v4 hook is a contract that runs custom logic around a pool's swaps and liquidity changes. Every pool records its hook address once, in its `Initialize` event, and every swap points back to its pool by ID. Join the two and you can rank hooks by pools and by real swap activity, which is the number that tells you which hooks people actually trade through.

## What it pulls

All of it comes from HyperSync.

- Every `Initialize` log on the v4 PoolManager, `0x8366a39cc670b4001a1121b8f6a443a643e40951` on Robinhood Chain or `0x000000000004444c5dc75cB358380D2e3dE08A90` on Ethereum, both from [Uniswap's v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments). The pool ID is the first topic and the hook is the third data word. A pool has a hook when that address isn't the zero address.
- Every `Swap` log on the PoolManager. Its first topic is the pool ID, which links it back to the pool and its hook.
- Block timestamps, to put pools and swaps in UTC months.

The hook with the most pools on Robinhood Chain, `0x4e3468951d49f2eea976ed0d6e75ffcb44a9a544`, is `DopplerHookInitializer`, listed in [Doppler's Robinhood Chain deployments](https://github.com/whetstoneresearch/doppler/blob/main/deployments/4663.md). You can look up other hooks on the [Robinhood Chain explorer](https://robinhoodchain.blockscout.com).

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py 110095000                # pools, hooks and every swap up to that block
python3 script.py 110095000 --pools-only   # pools and hooks only, a few minutes
python3 script.py --ethereum 26378070      # pool and hook counts for v4 on Ethereum
python3 script.py                          # up to the latest block
```

The swap count reads about 217M logs, so a full run takes a while. Add `--json` to also write `hooks.json` with pools per day and every hook's pool and swap counts. Sample output from block 110,095,000.

```
Uniswap v4 on Robinhood (chain 4663), blocks 0 to 110,095,000

Pools created            1,137,941
  with a hook              397,135  (34.9%)
Different hooks             31,823
  used by 2+ pools           3,365
  used by 10+ pools            771
Swaps                  216,981,683
  in pools with hook   108,945,756  (50.2%)

Top hooks by pools created:
  0x4e3468951d49f2eea976ed0d6e75ffcb44a9a544    234,684 pools   25,070,220 swaps
  0x48b8f6ad3a1b4aa477314c9a23035b8f84dde8cc     15,697 pools      131,356 swaps
  ...

Per month (UTC):          pools   with hook        swaps   in hooked pools
  2026-07       224,373      88,734   19,236,314    7,631,069
  2026-08       320,414      97,807   47,381,075   19,565,929
  2026-09       396,676     134,988  104,815,189   63,198,976
  2026-10       164,245      61,929   38,170,747   16,052,716
  ...
```

And with `--ethereum 26378070`.

```
Pools created              193,399
  with a hook               47,714  (24.7%)
Different hooks             11,311
  used by 2+ pools             937
  used by 10+ pools            272
```

With a fixed block the numbers won't change. On Ethereum the script stops after the pool counts and doesn't read swaps.

## Change the window or chain

- **Window.** Pass an end block. The start is always block 0, and months are UTC.
- **Chain.** `--ethereum` switches to Ethereum. For another chain, add its HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and its PoolManager from the [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments) next to the two at the top of the script.

## Check the numbers

The per-month pool column adds up to the pools created total, and the swap columns add up to the swap totals. To check one hook by hand, open a pool's `Initialize` transaction on the [Robinhood Chain explorer](https://robinhoodchain.blockscout.com/address/0x8366a39cc670b4001a1121b8f6a443a643e40951) and compare the `hooks` field with what the script decodes.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Initialize and
Swap event on the Uniswap v4 PoolManager on Robinhood Chain, then counts pools
and swaps per hook. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Add a --hook <address> option that prints, for that one hook, its pools with
their two token addresses and swap counts, sorted by swaps. Keep the standard
library only. Run it with end block 110095000 --hook
0x4e3468951d49f2eea976ed0d6e75ffcb44a9a544 and check that the pool count
matches the 234,684 in the main output.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Uniswap v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [Uniswap v4 multichain indexer with HyperIndex](https://docs.envio.dev/docs/HyperIndex/example-uniswap-v4-multi-chain-indexer)
- [Uniswap v4 hooks on Ethereum](../uniswap-v4-hooks-ethereum), the Ethereum example this one builds on
- [Envio Discord](https://discord.gg/envio)
