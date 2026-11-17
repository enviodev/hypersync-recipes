# Every Uniswap swap on Robinhood Chain

On 1 Nov 2026 (UTC), **Uniswap handled 1.05M swaps on Robinhood Chain**. 759K went through v4, 254K through v3 and 31K through v2. Pools that traded that day held 110 of the 203 Robinhood stock tokens.

| 1 Nov 2026 | Swaps |
| --- | --- |
| v4 | 759,332 |
| v3 | 254,479 |
| v2 | 31,282 |
| Total | 1,045,093 |

## Why it's interesting

Uniswap runs three different designs on Robinhood Chain. v4 keeps every pool in one PoolManager contract, while v2 and v3 deploy a contract per pool. This script shows how to count all three the same way, and how to keep forks out by only trusting pools that the official factories created.

It also links swaps back to Robinhood's stock token list, so you can see how much of the stock token catalogue is trading on Uniswap.

## What it pulls

All of it comes from HyperSync.

- `Initialize` logs from the v4 PoolManager `0x8366a39cc670b4001a1121b8f6a443a643e40951` ([v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)), with the pool ID and both tokens.
- `PoolCreated` logs from the v3 factory `0x1f7d7550b1b028f7571e69a784071f0205fd2efa` ([v3 deployments](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-robinhood-chain-deployments)) and `PairCreated` logs from the v2 factory `0x8bceaa40b9acdfaedf85adf4ff01f5ad6517937f` ([v2 deployments](https://developers.uniswap.org/docs/protocols/v2/deployments)).
- Every v4 `Swap` log on the PoolManager, and every v3 and v2 `Swap` log on the chain. A v2 or v3 swap only counts when its pool came from the official factory, so forks using the same event are left out.
- Block timestamps, to bucket swaps by hour.

The stock token list comes from the Robinhood API that the [stock tokens docs](https://docs.robinhood.com/chain/stock-tokens) point to (`https://api.robinhood.com/rhj/assets`), filtered to chain ID 4663.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py 2026-11-01 2026-11-02   # swaps from 00:00 UTC on 1 Nov to 00:00 UTC on 2 Nov
python3 script.py                         # every swap since launch
```

A one-day window takes about two minutes. With no dates it reads every swap since launch, which is hundreds of millions of logs and takes over an hour. Sample output from a run on 17 Nov 2026.

```
Robinhood Chain blocks 102,953,058 to 103,783,392
v4 pools 1,108,802
v3 pools 447,799
v2 pools 140,790
v4 swaps 759,332
v3 swaps 254,479
v2 swaps 31,282

Total Uniswap swaps 1,045,093
Robinhood stock tokens traded on Uniswap: 110 of 203
```

The pool counts always cover every pool up to the end of the window. On a full run with no dates, it also prints the date the running total passed 1M, 10M, 100M, 200M, 300M and 400M swaps, counted in days from 1 July 2026.

## Change the window or chain

- **Window.** Pass any two UTC dates. The script finds the first block at or after each midnight by binary search on block timestamps.
- **Chain.** Uniswap runs on many chains. Swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), and `POOL_MANAGER`, `V3_FACTORY` and `V2_FACTORY` for the addresses on Uniswap's deployment pages. The stock token step only makes sense on Robinhood Chain, so drop it elsewhere.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to count every Uniswap v2, v3 and
v4 swap on Robinhood Chain, keeping only pools made by the official factories.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a ranking of the 20 v4 pools with the most swaps in the window, with both
token addresses and whether either token is a Robinhood stock token. Keep the
standard library only. Run it for 2026-11-01 to 2026-11-02 and check that the
per-pool counts add up to the v4 total the script already prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Uniswap v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [Robinhood stock tokens](https://docs.robinhood.com/chain/stock-tokens)
- [Envio Discord](https://discord.gg/envio)
