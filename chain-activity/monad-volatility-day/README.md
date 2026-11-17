# Monad on a volatile market day

On 10 Nov 2026, the day a hotter than expected US inflation print landed at 13:30 UTC, **Monad's busiest hour carried 870K transactions, 3.9x its 30-day hourly average, with blocks still coming every 0.310s**. The median base fee held at 100 gwei through the busiest hours, and the busiest minute was 13:30 UTC with 21.8K transactions (364 TPS).

| 10 Nov 2026, 15:00 UTC | Busiest hour | 30-day baseline |
| --- | --- | --- |
| Transactions | 869,659 | 225,351 an hour on average |
| Block time | 0.310s | 0.303s |
| Median base fee | 100.0 gwei | |
| Gas used | 48.1% | 9.5% on average |

## Why it's interesting

A busy market day is a real-world load test. Reading every block and transaction for the day and the month before it shows how a chain's throughput, block times and fees behaved under load, hour by hour, against its own normal. The same script works for any day you want to look at.

## What it pulls

All of it comes from HyperSync.

- Every block on Monad for the day and the 30 days before it, with `timestamp`, `gas_used`, `gas_limit` and `base_fee_per_gas`.
- Every transaction in those blocks, with its block number and receipt `status`.

Hours and minutes are UTC, from each block's timestamp. Every transaction counts, including reverted ones (status 0), as on block explorers. Block time is an hour divided by the number of blocks in it. Gas used is total gas used over total gas limit. The median base fee is across the blocks in each hour, so a short spike shows in the max column and not in the median.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                  # 10 Nov 2026 against the 30 days before
python3 script.py 2026-11-05 14    # another day, against the 14 days before
```

The default run reads about 8.9M blocks and every transaction in them, in parallel, and takes about 20 minutes. Sample output, with some hours cut for length. The full run prints all 24.

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

The baseline covers 11 Oct to 9 Nov 2026. Both are in the past, so these numbers won't change.

## Change the window or chain

- **Day and baseline.** Pass a UTC date and a number of baseline days. The day has to be over on Monad already, or the script stops.
- **Chain.** Swap `HYPERSYNC` for another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks). On a chain with slower blocks, a bigger `CHUNK` keeps the number of parallel ranges sensible.

## Check the numbers

As a comparison, we checked the 10 Nov 15:00 hour (869,659 transactions in 11,629 blocks) and the 5 Nov 15:00 hour (674,624) block by block against Monad's public RPC with `eth_getBlockTransactionCountByNumber`, and both matched.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every block and
transaction on Monad for one UTC day and the days before it, then compares the
day hour by hour with that baseline. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a per-minute CSV for the chosen day, with transactions, blocks and the max
base fee in each minute, and print the 10 busiest minutes. Keep the standard
library only. Run it for 2026-11-10 with a 1-day baseline first and check that
the busiest minute still shows 21,813 transactions at 13:30 UTC.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Monad docs](https://docs.monad.xyz)
- [Envio Discord](https://discord.gg/envio)
