# Uniswap VolatilePair on Robinhood Chain

Reads every swap in Uniswap's VolatilePair ETH/USDG pool on Robinhood Chain with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints the number of swaps, USDG volume, swaps per day and the median LP fee the hook charged on each side of the market.

These are the numbers behind Envio's post on VolatilePair's first days on Robinhood Chain.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a block number to stop at a past snapshot. Block 104623299 is the last block of 2nd Nov 2026 UTC:

```bash
python script.py 104623299
```

## What it prints

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

## How it counts

- The PoolManager comes from Uniswap's [v4 deployments](https://developers.uniswap.org/docs/protocols/v4/deployments) page, and the pool ID from the [VolatilePair deployments](https://developers.uniswap.org/docs/protocols/uniswap-labs-hooks/volatile-pair/deployments) page.
- It reads the pool's Initialize event, then every Swap event for that pool ID.
- Volume is the USDG side of each swap. A swap that pays in USDG is a buy of ETH.
- The fee is the LP fee the hook set for that swap, as emitted in the Swap event.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Robinhood Chain
to read every Swap event from the Uniswap v4 PoolManager
(0x8366a39cc670b4001a1121b8f6a443a643e40951) for the VolatilePair ETH/USDG pool
(0xa791e5169faf703c0b63fd9552c33ec1128a773a00f5dc33a640da62a022cd35).
My API token is in the ENVIO_API_TOKEN environment variable.
Chart swaps per hour as a heatmap and compare the LP fee on buys and sells.
```
