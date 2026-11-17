# Stablecoins on Arc, 30 days of supply

Reads every USDC and EURC mint and burn on Arc with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints each token's supply now, 7 days ago and 30 days ago, how much was minted and burned in the last 30 days, and USDC's supply at the end of every day.

These are the numbers behind Envio's post on USDC supply on Arc growing $790.6M in 30 days.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Add an end time in UTC to rerun a past window exactly:

```bash
python script.py 2026-11-09T10:41:53
```

## What it prints

```
Stablecoins on Arc, up to 09 Nov 10:41 UTC (last mint or burn in block 30,336,014)
USDC: 1.287B now, 1.083B 7 days ago, 496.9M 30 days ago
      30 days: +790.6M net, 5.451B minted, 4.660B burned
EURC: 8.9M now, 7.1M 7 days ago, 7.6M 30 days ago
      30 days: +1.3M net, 90.5M minted, 89.2M burned
```

followed by USDC's supply at the end of each UTC day.

## How it counts

- Token addresses come from the [Arc contract addresses page](https://docs.arc.io/arc/references/contract-addresses): USDC `0x3600000000000000000000000000000000000000` and EURC `0xbEf5f6d51CB62b58e6A8f77868681825C6fe21c1`, both with 6 decimals.
- A mint is a Transfer from the zero address and a burn is a Transfer to it. Supply is mints minus burns since the first block.
- USDC is Arc's native asset. Its `totalSupply()` is 10,000 USDC above mints minus burns at every block we checked, from block 1,000 on, so the script adds that genesis balance.
- Only logs whose address and event signature match are counted.

## Checked against RPC

At block 30,336,095, `totalSupply()` from `https://rpc.mainnet.arc.io` returns 1,287,478,957.572406 USDC and 8,918,370.632218 EURC. Both match the script to the last unit. USDC also matches at blocks 25,000,000 and 30,000,000.

## Learn more

- [Arc on Envio](https://envio.dev/chains/arc): HyperSync and HyperIndex support for Arc
- [Index Arc with HyperIndex](https://docs.envio.dev/docs/HyperIndex/arc-testnet): build a full indexer and GraphQL API for Arc contracts
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
