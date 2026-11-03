# USDC on Arc, every mint and burn

Reads every USDC mint and burn on Arc with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints the supply at the start and end of a window, how much USDC was minted and burned in it, and how much of the burning went through Circle Gateway and CCTP.

These are the numbers behind Envio's post on USDC passing $1B on Arc.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py 30
```

The first argument is the number of days. Add an end time in UTC to rerun a past window exactly:

```bash
python script.py 30 2026-11-03T09:00:25
```

## What it prints

```
USDC on Arc, 30 days from 04 Oct 09:00 UTC to 03 Nov 09:00 UTC
Supply then  $513M
Minted       $4.40B
Burned       $3.80B
Supply now   $1.11B  (net $599M added)
  burned via Circle Gateway $1.28B
  burned via CCTP           $501M
  burned via other          $2.02B
```

## How it counts

- USDC on Arc is `0x3600000000000000000000000000000000000000`, from the [Arc docs](https://docs.arc.io).
- A mint is a Transfer from the zero address, and a burn is a Transfer to it. Supply is mints minus burns since the first block.
- Burns are labelled by the address that sent the USDC to the zero address. The Gateway and CCTP addresses come from Circle's [Gateway](https://developers.circle.com/gateway/references/contract-addresses) and [CCTP](https://developers.circle.com/cctp/references/contract-addresses) contract pages.
- Only logs whose address and event signature match are counted.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
USDC Transfer on Arc (0x3600000000000000000000000000000000000000) to or from the
zero address. My API token is in the ENVIO_API_TOKEN environment variable.
Work out USDC supply per day since launch, and chart how much was minted and
burned each day over the last 30 days.
```
