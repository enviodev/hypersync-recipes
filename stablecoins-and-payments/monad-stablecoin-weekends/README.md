# Stablecoins on Monad, weekdays and weekends

Reads every ERC-20 Transfer of Monad's USD stablecoins over the last 30 full UTC days with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints how much moved each day, how weekends compare with weekdays, the busiest day and the addresses that moved the most.

These are the numbers behind Envio's post on stablecoin activity on Monad.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a number of days and an end date (UTC, not included) to rerun a past window exactly:

```bash
python script.py 30 2026-11-10
```

The 30-day run reads about 11.5 million transfers in 32 parallel chunks.

## What it prints

```
Stablecoin transfers on Monad, 2026-10-11 to 2026-11-09 UTC (blocks 112,319,869 to 120,886,884)
11,506,430 transfers, $17.49B moved, 84,599 sending addresses

By token:  USDC $13.07B  AUSD $1.10B  USDT0 $988.2M  mUSD $1.26B  USD1 $0.7M  GHO $382.8M  USDe $689.8M

Weekend days: 9, $2.77B total, $307.8M a day, 318,571 transfers a day
Weekdays:     21, $14.72B total, $701.0M a day, 411,395 transfers a day
Weekend share of volume: 15.8%
Busiest day: 2026-10-13 (Tuesday), $1.33B
```

followed by the daily table and the top senders and receivers. The full output is in `out.txt`.

## How it counts

- Tokens are the dollar tokens on Monad's [tokens and bridges page](https://docs.monad.xyz/developer-essentials/network-information/tokens-and-bridges): USDC, AUSD, USDT0, mUSD, USD1, GHO and USDe. Staked and wrapped yield versions are left out. The USDC address `0x754704Bc059F8C67012fEd69BC8A327a5aafb603` also matches [Circle's list](https://developers.circle.com/stablecoins/usdc-contract-addresses).
- Every Transfer counts once at face value, including mints and burns. A payment that hops through a router counts at each hop, so this is transfer volume, not unique payment value.
- Only logs whose address and event signature match are kept. Days are UTC, from block timestamps.

## Checked against RPC

- Receipts: for 35 sampled blocks, `eth_getBlockReceipts` from `https://rpc.monad.xyz` returns the same stablecoin Transfer logs, log for log and value for value, as HyperSync.
- Supply: for all seven tokens, `totalSupply()` at block 112,319,868 and block 120,886,884 differs by exactly the net mints minus burns HyperSync sees in between.
- Concentration: no single address sent more than 5.9% of the volume, apart from the zero address (mints).

## Learn more

- [Monad on Envio](https://envio.dev/chains/monad): HyperSync and HyperIndex support for Monad
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
