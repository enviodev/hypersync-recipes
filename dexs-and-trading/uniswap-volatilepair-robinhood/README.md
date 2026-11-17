# Uniswap's VolatilePair pool on Robinhood Chain

From its first swap on 30 Oct 2026 to the end of 2 Nov 2026 (UTC), **Uniswap's VolatilePair ETH/USDG pool on Robinhood Chain did 68.5K swaps and $58.8M in USDG volume**. Swaps per day grew every day, from 6.8K on day one to 37.5K on 2 Nov. The median LP fee the hook charged was 1.58 bp on both buys and sells.

| Day (UTC) | Swaps |
| --- | --- |
| 30 Oct | 6,795 |
| 31 Oct | 10,179 |
| 1 Nov | 14,099 |
| 2 Nov | 37,450 |

## Why it's interesting

VolatilePair is a Uniswap v4 hook that sets the LP fee swap by swap. The fee isn't in the pool's config, it's in each `Swap` event, so the only way to see what traders actually paid is to read every swap. This script does that for one pool and splits it by side of the market.

The same pattern works for any v4 pool. Swap in a pool ID and you get its swaps, volume and fees.

## What it pulls

All of it comes from HyperSync.

- The pool's `Initialize` log on the v4 PoolManager `0x8366a39cc670b4001a1121b8f6a443a643e40951` ([v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)), to find the block the pool was created in.
- Every `Swap` log on the PoolManager for pool ID `0xa791e5169faf703c0b63fd9552c33ec1128a773a00f5dc33a640da62a022cd35`, the ETH/USDG pool listed on the [VolatilePair deployments page](https://developers.uniswap.org/docs/protocols/uniswap-labs-hooks/volatile-pair/deployments).
- Block timestamps, to group swaps by day.

Volume is the USDG side of each swap. A swap that pays in USDG is a buy of ETH, and one that pays in ETH is a sell. The fee is the `fee` field the hook set on that swap, in hundredths of a basis point, so the script divides by 100.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py             # up to the latest block
python3 script.py 104623299   # up to the last block of 2 Nov 2026 UTC, as above
```

Sample output with block 104623299.

```
VolatilePair ETH/USDG pool on Robinhood Chain, 30 Oct 11:40 UTC to 02 Nov 23:59 UTC
Swaps         68,523
USDG volume   $58,783,558
  2026-10-30  6,795 swaps
  2026-10-31  10,179 swaps
  2026-11-01  14,099 swaps
  2026-11-02  37,450 swaps
buy ETH   33,646 swaps, median LP fee 1.58 bp
sell ETH  34,877 swaps, median LP fee 1.58 bp
```

With a fixed block the numbers won't change. Without one, the pool keeps trading, so yours will be higher. Add a file name after the block (`python3 script.py 104623299 hourly.json`) and it also writes swaps per hour as JSON, for charting.

## Change the window or chain

- **Window.** Pass an end block as the first argument. The start is always the pool's `Initialize` block.
- **Pool.** Change `POOL_ID` to any other v4 pool ID on Robinhood Chain. If neither token is USDG, change the volume line, which reads `amount1` with 6 decimals.
- **Chain.** Swap the HyperSync `URL` for another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), and `POOL_MANAGER` for that chain's address on the [v4 deployments page](https://developers.uniswap.org/docs/protocols/v4/deployments).

## Check the numbers

The buy and sell counts should add up to the total swaps (33,646 + 34,877 = 68,523). To check a single swap, open a recent `Swap` log for the pool on the [Robinhood Chain explorer](https://robinhoodchain.blockscout.com/address/0x8366a39cc670b4001a1121b8f6a443a643e40951) and compare its `amount1` and `fee` with what the script decodes.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Swap for one
Uniswap v4 pool on Robinhood Chain and reports volume and the LP fee the
VolatilePair hook charged. My HyperSync token is in the ENVIO_API_TOKEN
environment variable.

Add an estimate of LP fees in USDG, worked out per swap as the USDG side times
the fee, and print them per day next to the swap counts. Keep the standard library
only. Run it with end block 104623299 and check that the daily swap counts still
add up to 68,523.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [VolatilePair deployments](https://developers.uniswap.org/docs/protocols/uniswap-labs-hooks/volatile-pair/deployments)
- [Uniswap v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments)
- [Envio Discord](https://discord.gg/envio)
