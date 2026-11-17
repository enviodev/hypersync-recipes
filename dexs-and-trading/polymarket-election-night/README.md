# Polymarket on US election night

Reads every `OrdersMatched` event on Polymarket's exchange contracts on Polygon with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and adds up the USDC traded hour by hour from 1pm to 3am US Eastern time on a night and on each of the seven nights before it.

These are the numbers behind Envio's US election night post.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py 2026-11-03
```

Pass any date to look at a different night. It reads about 6.7 million trades across 8 nights in parallel, which takes about 8 minutes. Hours are US Eastern time, so nights either side of a clock change line up correctly.

## What it prints

```
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

## How it counts

- Contracts: CTF Exchange, Neg Risk CTF Exchange and Exchange V3, from [Polymarket's deployment docs](https://docs.polymarket.com/developers/CTF/deployment-resources).
- Volume is the taker side of each match, in USDC. A buy counts the maker amount filled and a sell counts the taker amount filled.
- Only logs whose address and event signature match are counted.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
OrdersMatched event from Polymarket's exchange contracts on Polygon
(https://docs.polymarket.com/developers/CTF/deployment-resources) for the last 7 days.
My API token is in the ENVIO_API_TOKEN environment variable.
Add up the taker-side USDC per hour and show me which hours of the day are busiest,
as a heatmap with one row per day.
```
