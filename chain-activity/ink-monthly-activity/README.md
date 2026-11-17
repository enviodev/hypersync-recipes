# Ink transactions and active addresses by month

Reads every Ink transaction since 1 January 2026 with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), buckets each one by its block's UTC month, and counts transactions and unique senders per month. The last month is also split by day so you can see its daily pace.

These are the numbers behind Envio's post on Ink's 2026 activity, a reply to Optimism's post on Ink's year so far.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

By default it runs to the current chain head. To reproduce the numbers below exactly, pin the end block:

```bash
END_BLOCK=60840178 python script.py
```

It reads about 180 million transactions, so a full run takes around 15 minutes. `ink_monthly.json` gets the same numbers.

## What it prints

```
Ink, 1 Jan 2026 to block 60,840,178 (2026-11-10 19:23 UTC)
month          all txs      user txs  deposit txs  active addresses
2026-01     14,166,223    11,485,880    2,680,343           259,801
2026-02     24,215,612    21,794,722    2,420,890           514,178
2026-03     17,611,143    14,930,812    2,680,331           107,904
2026-04     14,737,193    12,143,530    2,593,663           123,549
2026-05     10,959,771     8,279,731    2,680,040            80,313
2026-06     15,495,776    12,901,949    2,593,827            76,123
2026-07      9,840,848     7,160,929    2,679,919            69,523
2026-08     19,704,293    17,024,206    2,680,087           164,342
2026-09     24,260,752    21,667,115    2,593,637           124,109
2026-10     15,058,268    12,378,368    2,679,900           100,688
2026-11     12,210,497    11,362,629      847,868            39,833
total      178,260,376   151,129,871   27,130,505           924,415 unique over the whole period
User transactions per UTC day in 2026-11 (the last day may be partial)
  2026-11-01      382,870
  2026-11-02      449,584
  2026-11-03    1,552,029
  2026-11-04    1,429,220
  2026-11-05    1,310,384
  2026-11-06    1,201,856
  2026-11-07      971,187
  2026-11-08    1,137,915
  2026-11-09    1,632,555
  2026-11-10    1,295,029
```

In the first ten days of November, Ink handled 11.4M user transactions, nearly October's 12.4M for the whole month. From 3 to 9 November it averaged 1.3M a day, more than three times October's average of about 399K.

## How it counts

- Ink is chain ID 57073 and HyperSync serves it at `https://ink.hypersync.xyz`.
- Month and day boundaries are the first block with a timestamp at or after midnight UTC, found by binary search. Ink makes a block every second, so 1 January 2026 starts at block 33,727,189.
- The query selects every transaction (`"transactions": [{}]`) with only the `from` and `type` fields, using HyperSync's default join mode.
- "User txs" leaves out type 126 (0x7e) deposit transactions. Every OP Stack block starts with one of these, the L1 info transaction, sent from `0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001`. On one-second blocks that is about 86,400 a day, so "all txs" runs about 27M higher over the year.
- "Active addresses" is the number of unique `from` addresses on user transactions in that month. The total line counts each address once across the whole period.
- The last month is partial and grows until the month ends.

## Checks

- We compared HyperSync's transaction count with `eth_getBlockTransactionCountByNumber` on Ink's public RPC (`https://rpc-gel.inkonchain.com`) for 20 random blocks between January and November and a run of 300 consecutive blocks from block 50,000,000. Every block matched.
- Optimism's post on 10 November gave Ink 137M transactions year to date. Our count of user transactions passes 137M on 25 October and reaches 151M by 10 November. Counting deposit transactions too, it would have passed 137M in September, so the published figure lines up with user transactions.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Ink (chain ID 57073,
https://ink.hypersync.xyz) transaction since 1 January 2026 with just the from and type fields. My API
token is in the ENVIO_API_TOKEN environment variable. Leave out type 126 deposit transactions, then count
transactions and unique senders per UTC month and chart them as monthly columns.
```

## Learn more

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query): transaction selection, field selection and paging
