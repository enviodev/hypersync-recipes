# Polymarket on US election day

Between 00:00 and 12:00 UTC on 3 Nov 2026, **Polymarket traded $49.5M on Polygon, 38% more than the average of the six mornings before**. Trade count only rose 8%, so most of the jump came from bigger trades, with the average trade going from $57 to $73.

| Morning (00:00 to 12:00 UTC) | Volume | Trades | Avg trade |
| --- | --- | --- | --- |
| Wed 28 Oct | $35.1M | 638,137 | $55 |
| Thu 29 Oct | $39.8M | 685,351 | $58 |
| Fri 30 Oct | $31.2M | 625,487 | $50 |
| Sat 31 Oct | $40.2M | 725,912 | $55 |
| Sun 1 Nov | $31.3M | 495,411 | $63 |
| Mon 2 Nov | $38.1M | 589,738 | $65 |
| Tue 3 Nov | $49.5M | 678,052 | $73 |

## Why it's interesting

Every Polymarket trade settles onchain as an `OrdersMatched` event, so you can measure how a real-world event moves trading straight from the chain. Comparing the same hours across a week also keeps time-of-day patterns out of the comparison.

## What it pulls

All of it comes from HyperSync.

- Every `OrdersMatched` log from Polymarket's three exchange contracts on Polygon, from [Polymarket's deployment docs](https://docs.polymarket.com/developers/CTF/deployment-resources). They are the CTF Exchange `0xE111180000d2663C0091e4f400237545B87B996B`, the Neg Risk CTF Exchange `0xe2222d279d744050d28e00520010520000310F59` and Exchange V3 `0xe3333700cA9d93003F00f0F71f8515005F6c00Aa`.
- Block timestamps, to find the first block at or after 00:00 and 12:00 UTC by binary search.

Volume is the taker side of each match, in USDC. A buy counts the maker amount filled and a sell counts the taker amount filled. A trade is one `OrdersMatched` event.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py 2026-11-03
```

It reads seven mornings in parallel, about 4.5M trades, and takes about 8 minutes. Sample output.

```
Reading 7 mornings in parallel, this takes a few minutes...
Wed 28 Oct  $  35.1M   638,137 trades  $   55 avg trade
Thu 29 Oct  $  39.8M   685,351 trades  $   58 avg trade
Fri 30 Oct  $  31.2M   625,487 trades  $   50 avg trade
Sat 31 Oct  $  40.2M   725,912 trades  $   55 avg trade
Sun 01 Nov  $  31.3M   495,411 trades  $   63 avg trade
Mon 02 Nov  $  38.1M   589,738 trades  $   65 avg trade
Tue 03 Nov  $  49.5M   678,052 trades  $   73 avg trade

2026-11-03: $49.5M by midday UTC, +38% vs the 6-day average, trades +8%, average trade $57 -> $73
```

The window is fixed by the date, so these numbers won't change. The $57 is the average trade across all six earlier mornings together.

## Change the window or chain

- **Day.** Pass any date. The script compares 00:00 to 12:00 UTC on that day with the same hours on each of the six days before. With no date it uses today, which may not have reached midday yet.
- **Hours.** The window length is the `12 * 3600` in `morning()`. Change it, or the start hour in the `dt.datetime(...)` line, to look at a different part of the day.
- **Chain.** Polymarket runs on Polygon. To use the same approach for another exchange, swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and the contracts and event for that exchange's.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every OrdersMatched
event from Polymarket's exchange contracts on Polygon and adds up taker-side
USDC for the same 12 hours on seven days. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Change it to report volume for every UTC hour of the last 7 full days, as a grid
with one row per day and one column per hour, and print the five busiest hours.
Keep the standard library only. Then check that the hours for one day add up to
that day's total.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Polymarket contract addresses](https://docs.polymarket.com/developers/CTF/deployment-resources)
- [Polymarket on US election night](../polymarket-election-night), the same data hour by hour through the night
- [Envio Discord](https://discord.gg/envio)
