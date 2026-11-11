# Monad on a volatile market day

Reads every block and every transaction on Monad for one UTC day and the 30 days before it with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then compares the day hour by hour with that baseline: transactions, block times, gas used, base fee and reverted transactions.

The default day is 10 November 2026, when a hotter than expected US inflation print at 13:30 UTC pushed crypto prices lower. These are the numbers behind Envio's post on how Monad handled it.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a day and a baseline length to look at another day, for example `python script.py 2026-11-05 14`. The default run reads about 8.9 million blocks and every transaction in them, in parallel, and takes about 20 minutes.

## What it prints

```
Monad, blocks 112319869 to 121171339: 30 days before 2026-11-10 (baseline), then 2026-11-10

Baseline: 225,351 transactions an hour on average, busiest hour 05 Nov 15:00 UTC with 674,624
          busiest minute 14 Oct 12:30 UTC with 22,711 (379 TPS)
          one block every 0.303s, blocks 9.5% full on average, 3.15% of transactions reverted

2026-11-10 by hour (UTC)
  hour    transactions  vs baseline  blocks  block time  gas used  median base fee  max base fee  reverted
  00:00        344,858         1.5x  11,888      0.303s     13.5%        100.0 gwei     101.7 gwei     1.59%
  ...
  12:00        352,947         1.6x  11,849      0.304s     14.8%        100.0 gwei     109.3 gwei     1.65%
  13:00        519,168         2.3x  11,859      0.304s     23.9%        100.0 gwei     254.7 gwei     3.97%
  14:00        707,796         3.1x  11,688      0.308s     40.1%        100.0 gwei     224.6 gwei     3.30%
  15:00        869,659         3.9x  11,629      0.310s     48.1%        100.0 gwei     196.2 gwei     3.00%
  16:00        760,614         3.4x  11,825      0.304s     41.3%        100.0 gwei     140.7 gwei     2.15%
  17:00        633,167         2.8x  11,832      0.304s     34.7%        100.0 gwei     111.8 gwei     1.68%
  ...
  23:00        315,512         1.4x  11,881      0.303s     12.5%        100.0 gwei     103.4 gwei     1.53%

Busiest hour: 10 Nov 15:00 UTC, 869,659 transactions, 3.9x the baseline hourly average and 1.3x the baseline's busiest hour
  blocks every 0.310s (baseline 0.303s), median base fee 100.0 gwei
Busiest minute: 10 Nov 13:30 UTC, 21,813 transactions (364 TPS)
```

The baseline covers 11 October to 9 November 2026. The full run prints all 24 hours.

## How it counts

- Hours and minutes are UTC, taken from each block's timestamp. A transaction belongs to the hour of the block it landed in.
- Every transaction counts, including reverted ones, as on block explorers. Reverted means a receipt status of 0.
- Block time is an hour divided by the number of blocks in it. Gas used is total gas used over total gas limit.
- The base fee is the block's `base_fee_per_gas`. The median is across the blocks in each hour, so a short spike shows in the max column and not in the median.
- Transactions are not users. In the busiest hour on 10 November, 493,159 of the 869,659 transactions were sent to FastLane contracts listed in the Monad Foundation's [protocol registry](https://github.com/monad-crypto/protocols).
- We checked the 10 November 15:00 hour (869,659 transactions in 11,629 blocks) and the 5 November 15:00 hour (674,624) block by block against Monad's public RPC with `eth_getBlockTransactionCountByNumber`, and both matched.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every block and transaction
on Monad (https://monad.hypersync.xyz) for the last 7 days. My API token is in the ENVIO_API_TOKEN
environment variable. Chart transactions per minute and the median base fee per hour, and mark the
10 busiest minutes.
```
