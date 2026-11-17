# Ondo Intelligent Portfolios

Reads every mint, burn and transfer of Ondo's Intelligent Portfolio tokens on Ethereum and BNB Chain with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints how much each portfolio holds, how many addresses hold them, and how much arrived since a date you choose.

These are the numbers behind Envio's post on Ondo Intelligent Portfolios passing $50M.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Pass a UTC date to change the "arrived since" cut-off, for example `python script.py 2026-10-01`.

## What it prints

```
Ondo Intelligent Portfolios on Ethereum and BNB Chain: $54.7M
  BLKGRWon   $ 15.72M  28.8%
  MAG7Xon    $ 15.37M  28.1%
  ...
Addresses holding a portfolio token: 1,840
Arrived since 12 Oct 2026: $47.0M (86%)
```

## How it counts

- Token addresses come from each portfolio's page on [app.ondo.finance](https://app.ondo.finance/?tab=intelligent-portfolios).
- Supply is mints minus burns. It matches each token's `totalSupply` onchain.
- Dollar values use the token prices shown on Ondo's app on 4th Nov 2026. Edit `PRICES` for today's value.
- Solana isn't included.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Transfer of Ondo's Intelligent Portfolio tokens on Ethereum (addresses are on each
portfolio's page at app.ondo.finance). My API token is in the ENVIO_API_TOKEN
environment variable. Chart each portfolio's supply over time and how many
addresses hold it.
```
