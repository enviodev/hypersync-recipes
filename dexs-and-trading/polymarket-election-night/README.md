# Polymarket on US election night

From 1pm on 3 Nov 2026 to 3am the next morning, US Eastern time, **Polymarket traded $96.3M on Polygon, 52% more than the $63.4M average of the seven nights before**. The busiest hour was 6pm ET with $11.95M, 2.3x a normal 6pm, and the average trade went from $78 to $98.

| Night (1pm to 3am ET) | Volume | Trades | Avg trade |
| --- | --- | --- | --- |
| Tue 27 Oct | $56.5M | 822,318 | $69 |
| Wed 28 Oct | $77.7M | 917,086 | $85 |
| Thu 29 Oct | $52.4M | 764,324 | $69 |
| Fri 30 Oct | $64.7M | 902,935 | $72 |
| Sat 31 Oct | $70.9M | 739,765 | $96 |
| Sun 1 Nov | $55.9M | 738,523 | $76 |
| Mon 2 Nov | $65.6M | 822,727 | $80 |
| Tue 3 Nov | $96.3M | 978,923 | $98 |

## Why it's interesting

Every Polymarket trade settles onchain as an `OrdersMatched` event, so you can follow a night of news hour by hour straight from the chain. Comparing each hour with the same hour on the nights before shows which moments actually moved trading.

## What it pulls

All of it comes from HyperSync.

- Every `OrdersMatched` log from Polymarket's three exchange contracts on Polygon, from [Polymarket's deployment docs](https://docs.polymarket.com/developers/CTF/deployment-resources). They are the CTF Exchange `0xE111180000d2663C0091e4f400237545B87B996B`, the Neg Risk CTF Exchange `0xe2222d279d744050d28e00520010520000310F59` and Exchange V3 `0xe3333700cA9d93003F00f0F71f8515005F6c00Aa`.
- Block timestamps, to put each trade in its hour.

Volume is the taker side of each match, in USDC. A buy counts the maker amount filled and a sell counts the taker amount filled. Hours are US Eastern time, so nights either side of a clock change still line up. "A normal 6pm" is the average of that hour over the seven nights before.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py 2026-11-03
```

It reads eight nights in parallel, about 6.7M trades, and takes about 8 minutes. Sample output.

```
Reading 8 nights in parallel, this takes a few minutes...
Tue 27 Oct  $  56.5M   822,318 trades  $   69 avg trade
Wed 28 Oct  $  77.7M   917,086 trades  $   85 avg trade
Thu 29 Oct  $  52.4M   764,324 trades  $   69 avg trade
Fri 30 Oct  $  64.7M   902,935 trades  $   72 avg trade
Sat 31 Oct  $  70.9M   739,765 trades  $   96 avg trade
Sun 01 Nov  $  55.9M   738,523 trades  $   76 avg trade
Mon 02 Nov  $  65.6M   822,727 trades  $   80 avg trade
Tue 03 Nov  $  96.3M   978,923 trades  $   98 avg trade

2026-11-03: $96.3M from 1pm to 3am ET, +52% vs the 7-night average of $63.4M
Busiest hour 6pm ET, $11.95M, 2.3x a normal 6pm
Average trade $78 -> $98
```

The window is fixed by the date, so these numbers won't change.

## Change the window or chain

- **Night.** Pass the date the night starts on. The script compares 1pm to 3am Eastern from that date with the same hours on each of the seven nights before. With no date it uses yesterday in Eastern time.
- **Hours.** `HOURS` sets how many hours to read, and the `13` in `night()` is the start hour in Eastern time. Change `ET` to another time zone name, such as `Europe/London`, to line hours up with a different market.
- **Chain.** Polymarket runs on Polygon. To use the same approach for another exchange, swap `URL` for that chain's HyperSync endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and the contracts and event for that exchange's.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every OrdersMatched
event from Polymarket's exchange contracts on Polygon and adds up taker-side
USDC per Eastern-time hour across eight nights. My HyperSync token is in the
ENVIO_API_TOKEN environment variable.

Add a table with one row per hour for the chosen night, showing its volume, the
average for that hour over the seven nights before, and the ratio. Write it to
hourly.csv as well. Keep the standard library only. Run it for 2026-11-03 and
check that the 6pm row matches the busiest hour line the script already prints.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Polymarket contract addresses](https://docs.polymarket.com/developers/CTF/deployment-resources)
- [Polymarket on US election day](../polymarket-election-day), the same data for the morning
- [Envio Discord](https://discord.gg/envio)
