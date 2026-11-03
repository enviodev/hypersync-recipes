# Polymarket on US election day

Reads every `OrdersMatched` event on Polymarket's exchange contracts on Polygon with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and adds up the USDC traded from 00:00 to 12:00 UTC on a day and on each of the six days before it.

These are the numbers behind Envio's US election day post.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py 2026-11-03
```

Pass any date to look at a different morning. It reads about 4.5 million trades across 7 mornings in parallel, which takes about 8 minutes.

## What it prints

```
Wed 28 Oct  $  35.1M   638,137 trades  $   55 avg trade
Thu 29 Oct  $  39.8M   685,351 trades  $   58 avg trade
Fri 30 Oct  $  31.2M   625,487 trades  $   50 avg trade
Sat 31 Oct  $  40.2M   725,912 trades  $   55 avg trade
Sun 01 Nov  $  31.3M   495,411 trades  $   63 avg trade
Mon 02 Nov  $  38.1M   589,738 trades  $   65 avg trade
Tue 03 Nov  $  49.5M   678,052 trades  $   73 avg trade

2026-11-03: $49.5M by midday UTC, +38% vs the 6-day average, trades +8%, average trade $57 -> $73
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
