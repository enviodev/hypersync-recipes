# Ink transactions and active addresses by month

From 1 Jan 2026 to block 60,840,178 (10 Nov 2026), **Ink handled 151M user transactions from 924K unique addresses**. In the first ten days of November it did 11.4M, close to October's 12.4M for the whole month. From 3 to 9 November it averaged 1.3M a day, more than three times October's 399K.

| Month | User txs | Active addresses |
| --- | --- | --- |
| 2026-08 | 17,024,206 | 164,342 |
| 2026-09 | 21,667,115 | 124,109 |
| 2026-10 | 12,378,368 | 100,688 |
| 2026-11 (to 10 Nov) | 11,362,629 | 39,833 |
| 1 Jan to 10 Nov 2026 | 151,129,871 | 924,415 |

## Why it's interesting

Counting a chain's transactions sounds simple until you hit system transactions. Every OP Stack block starts with a deposit transaction, the L1 info transaction, and on Ink's one-second blocks that's about 86,400 a day, or 27M from January to 10 November. This script reads every transaction with just two fields, splits those out and counts unique senders, which works for any OP Stack chain.

## What it pulls

All of it comes from HyperSync.

- Every transaction on Ink (chain ID 57073) since 1 January 2026, with only the `from` and `type` fields. The query selects them all with `"transactions": [{}]`.
- Block timestamps, to find the first block of each UTC month and of each day in the last month by binary search. 1 January 2026 starts at block 33,727,189.

"User txs" leaves out type 126 (`0x7e`) deposit transactions, which include the L1 info transaction sent from `0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001`. "Active addresses" is the number of unique `from` addresses on user transactions in that month, and the total line counts each address once across the whole period.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                        # up to the latest block
END_BLOCK=60840178 python3 script.py     # up to the block used above
```

It reads about 180M transactions, so a full run takes around 15 minutes. It also writes the same numbers to `ink_monthly.json`. Sample output with `END_BLOCK=60840178`.

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

With `END_BLOCK` set the numbers won't change. Without it, the last month is partial and grows until the month ends.

## Change the window or chain

- **Window.** `END_BLOCK` pins the end (exclusive). `YEAR` at the top of `script.py` sets the year, and the script counts from 1 January of that year to the month of the end block. Keep the end block in the same year.
- **Chain.** Swap `BASE` for another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks). `DEPOSIT_TYPE` only applies to OP Stack chains, so on other chains "user txs" and "all txs" will match.

## Check the numbers

- As a comparison, we checked HyperSync's transaction count against `eth_getBlockTransactionCountByNumber` on Ink's public RPC (`https://rpc-gel.inkonchain.com`) for 20 random blocks between January and November, and for 300 consecutive blocks from block 50,000,000. Every block matched.
- Optimism's own post on 10 November gave Ink 137M transactions year to date. Our user transaction count passes 137M on 25 October and reaches 151M by 10 November. Counting deposit transactions too, it would have passed 137M in September, so that outside figure lines up with user transactions.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Ink transaction
since 1 January 2026 with only the from and type fields, then counts
transactions and unique senders per UTC month. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a "new addresses" column, counting senders whose first user transaction of
the year falls in that month. Keep the standard library only. Run it with
END_BLOCK=60840178 and check that the new addresses column adds up to the
924,415 unique senders on the total line.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Ink docs](https://docs.inkonchain.com)
- [Envio Discord](https://discord.gg/envio)
