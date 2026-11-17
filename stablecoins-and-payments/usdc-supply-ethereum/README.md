# USDC supply on Ethereum

Reads every USDC mint and burn on Ethereum with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and prints how much USDC was added or removed each day.

These are the numbers behind Envio's post on USDC on Ethereum shrinking by $2.3B in a month.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py 30
```

The argument is the number of days to look back.

## What it prints

```
python script.py 30 2026-11-04
Net USDC minted or burned on Ethereum per UTC day, 05 Oct to 03 Nov
05 Oct      -52.7M USDC
...
03 Nov     -404.0M USDC
Minted    25.10B USDC
Burned    27.32B USDC
Total moved in and out  52.42B USDC, net -2.22B
```

The first argument is the number of days. The optional second argument is an end date (exclusive) to rerun a past window exactly. Without it, the window ends today and the last day is partial.

## How it counts

- USDC on Ethereum is `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`, from [Circle's contract addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses).
- A mint is a Transfer from the zero address, and a burn is a Transfer to it.
- The totals match the contract's own `totalSupply()` read at the first block of each day.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
USDC Transfer on Ethereum (0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48) to or from the
zero address over the last 90 days. My API token is in the ENVIO_API_TOKEN environment
variable. Chart USDC minted and burned per day, and the running supply.
```
