# Uniswap v4 hooks on Robinhood

Reads every pool created on Uniswap v4 on Robinhood with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), notes which hook each pool uses, and counts every swap. It prints how many pools use a hook, how many different hook contracts there are, the most used hooks by pools and by swaps, and pools and swaps per month. The same script counts pools and hooks on Ethereum, so you can compare the two.

These are the numbers behind Envio's post on Uniswap v4 hooks on Robinhood.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a block number to stop at a fixed block and get the exact numbers from the post:

```bash
python script.py 110095000              # pools, hooks and every swap (about 217M swaps, so it takes a while)
python script.py 110095000 --pools-only # pools and hooks only, a few minutes
python script.py --ethereum 26378070    # the same pool and hook counts on Ethereum
```

## What it prints

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

And for Ethereum, up to block 26,378,070:

```
Pools created              193,399
  with a hook               47,714  (24.7%)
Different hooks             11,311
  used by 2+ pools             937
  used by 10+ pools            272
```

## How it counts

- Both PoolManagers come from Uniswap's [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments): `0x8366a39cc670b4001a1121b8f6a443a643e40951` on Robinhood (chain 4663) and `0x000000000004444c5dc75cB358380D2e3dE08A90` on Ethereum.
- Every pool starts with an `Initialize` event on the PoolManager. A pool uses a hook when the `hooks` address in that event isn't the zero address. A hook contract counts once, however many pools use it.
- Every `Swap` event on the PoolManager is one swap. It belongs to the pool whose id is in its first topic, and counts as a swap through a hook when that pool has one.
- Months are UTC. The first Robinhood v4 pool was created in May 2026 and the first Ethereum one in January 2025.
- The most used hook by pools, `0x4e34...a544`, is `DopplerHookInitializer`, listed in [Doppler's Robinhood deployments](https://github.com/whetstoneresearch/doppler/blob/main/deployments/4663.md). Contract names for other hooks can be read on the [Robinhood block explorer](https://robinhoodchain.blockscout.com).

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Initialize and Swap event on the Uniswap v4 PoolManager on Robinhood (chain 4663,
0x8366a39cc670b4001a1121b8f6a443a643e40951, endpoint https://robinhood.hypersync.xyz).
My API token is in the ENVIO_API_TOKEN environment variable. Count pools with and
without a hook, the number of different hook contracts, and the 10 hooks with the
most pools and the most swaps.
```

## Learn more

- [Robinhood on Envio](https://envio.dev/chains/robinhood): HyperSync and HyperIndex support for Robinhood
- [Index Robinhood data with HyperIndex](https://docs.envio.dev/blog/index-robinhood-chain-data): a step-by-step tutorial
- [Live apps on Robinhood, verified onchain](https://docs.envio.dev/blog/robinhood-chain-ecosystem): the apps building there, with an open source indexer ([repo](https://github.com/enviodev/robinhood-ecosystem-indexer))
- [Uniswap v4 multichain indexer example](https://docs.envio.dev/docs/HyperIndex/example-uniswap-v4-multi-chain-indexer): index v4 pools and swaps across chains ([repo](https://github.com/enviodev/uniswap-v4-indexer))
- [Uniswap v4 hooks on Ethereum](https://github.com/enviodev/hypersync-recipes/tree/main/uniswap-v4-hooks-ethereum): the Ethereum recipe this one builds on
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
