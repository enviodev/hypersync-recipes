# Coinbase tokenized stocks on Aero (Base)

Finds every Aero pool on Base that holds a Coinbase tokenized stock, then reads every swap in those pools with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints the USDC-paired volume per stock and how much of it traded while US stock markets were closed.

These are the numbers behind Envio's post on tokenized stock trading on Aero.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py 7
```

The first argument is the number of days. Add an end time in UTC to rerun a past window exactly:

```bash
python script.py 7 2026-11-04T09:40:09
```

## What it prints

```
Coinbase tokenized stocks on Aero (Base), 28 Oct 09:40 UTC to 04 Nov 09:40 UTC
Pools holding a stock: 1,997
USDC-paired volume: $780.3M, 77.5% while US markets were closed
  MSTRc    $  135.7M   70.5% closed
  SNDKc    $  131.8M   79.4% closed
  METAc    $   76.6M   79.6% closed
  ...
```

## How it counts

- Stock tokens come from Coinbase's [Tokenized Stocks API](https://docs.base.org/sdks/tokenized-stocks/overview).
- Pools come from the PoolCreated events of the Aerodrome classic and Slipstream factories ([contracts](https://github.com/aerodrome-finance/contracts), [Slipstream](https://github.com/aerodrome-finance/slipstream)) and the Aero CL factory ([deployment addresses](https://github.com/dromos-labs/metadex-slipstream-public/blob/main/deployment-addresses/cl-base.json)).
- Volume is the USDC side of each swap in a stock/USDC pool. Swaps against other tokens are not priced.
- US markets count as open 9:30am to 4pm ET on weekdays.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every swap
in Aero pools on Base that hold a Coinbase tokenized stock
(token list: https://api.coinbase.com/v1/tokenized-stocks). My API token is in the
ENVIO_API_TOKEN environment variable. Chart USDC volume per stock per hour for the last
7 days, and shade the hours when US stock markets were open.
```
