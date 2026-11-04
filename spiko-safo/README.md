# Spiko SAFO on Ethereum, Arbitrum, Polygon and Base

Reads every Transfer of every Spiko SAFO share class on Ethereum, Arbitrum, Polygon and Base with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It rebuilds each share class's supply from its mints and burns, counts holders, and values everything in dollars using Spiko's own NAVs and FX rates.

These are the numbers behind Envio's post on Spiko SAFO.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

```
Spiko SAFO on Ethereum, Arbitrum, Polygon and Base
  Arbitrum  $  474.9M    93% in euro classes   494 holders
  Ethereum  $  138.8M    48% in euro classes    38 holders
  Polygon   $   94.5M    84% in euro classes   507 holders
  Base      $   19.0M    83% in euro classes   118 holders
Total $727.2M, 83% in euro share classes, 1157 holders across the four chains
```

The numbers move as people subscribe and redeem, so yours will differ a little.

## How it counts

- Share classes and token addresses come from Spiko's [public API](https://docs.spiko.io/developers/public_api/getting_started) (`/share-classes/`, SAFO fund only). That covers the dollar, euro, pound and franc classes, including the D classes.
- Supply is every mint minus every burn on each chain. It matches each token's `totalSupply` onchain.
- Values use Spiko's latest NAV per share class and Spiko's EUR, GBP and CHF to USD rates from the same API.
- Holders are addresses with a positive balance on each chain, so an address that holds on two chains counts twice. Some holders are contracts.
- SAFO is also issued on Stellar, Starknet, Solana and Etherlink. This script only reads the four EVM chains above, so its total is a part of the whole fund.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) and Spiko's public API
(https://public-api.spiko.io/v0/share-classes/) to read every Transfer of the Spiko SAFO share
classes on Ethereum, Arbitrum, Polygon and Base. My API token is in the ENVIO_API_TOKEN
environment variable. Chart SAFO supply in dollars per chain, week by week, split by currency.
```
