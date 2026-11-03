# New UNI holders per day

Reads every UNI Transfer on Ethereum since the token launched in 2020 with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and counts how many addresses send or receive UNI for the first time each day.

These are the numbers behind Envio's post on the busiest day for new UNI holders since its first week.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

It works for any ERC-20. Pass the token address and an optional start block:

```bash
python script.py 0xTokenAddress 12345678
```

It writes `new_addresses.csv` with one row per day and prints the busiest days.

## What it prints

```
1,693,450 addresses in total. Busiest days for new addresses:
  2020-09-17  178,331
  2020-09-18  53,692
  2020-09-19  18,600
  2026-10-27  13,137
  2020-09-20  9,872
```

## How it counts

- UNI is `0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984`, the UNI token contract ([Etherscan](https://etherscan.io/token/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984)).
- An address counts on the UTC day it first appears as the sender or receiver of a UNI Transfer. The zero address is skipped.
- Only logs whose address and event signature match are counted.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Transfer of UNI (0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984) on Ethereum since 2020.
My API token is in the ENVIO_API_TOKEN environment variable.
Count how many addresses send or receive UNI for the first time each day, and
show me the busiest days as a calendar heatmap.
```
