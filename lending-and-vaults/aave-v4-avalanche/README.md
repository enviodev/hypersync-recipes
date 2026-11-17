# Aave v4 on Avalanche

Reads every deposit and withdrawal on the Aave v4 Hub on Avalanche with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It prints what's deposited by asset, how many addresses have supplied, and the biggest single day for stablecoin deposits.

These are the numbers behind Envio's post on Aave v4 deposits passing $125M on Avalanche.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

## What it prints

```
Aave v4 on Avalanche, first deposit 15 Jul 2026
  USDt    $55.7M
  USDe    $34.2M
  USDC    $8.6M
  WAVAX   1,849,339.03 WAVAX
  ...
Addresses that have supplied: 1,114
Biggest stablecoin day: 01 Nov 2026, +$17.1M USDe, +$48.1M USDt
```

The numbers grow as people deposit, so yours will be a little higher.

## How it counts

- Hub and spoke addresses come from the [Aave address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV4Avalanche.sol).
- Deposits are the Hub's Add events minus its Remove events, per asset.
- Addresses are every supplier on the spokes plus every depositor into the ERC-4626 vaults.
- Stablecoins are counted at $1. Other assets are shown in their own units.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
Add and Remove event on the Aave v4 Hub on Avalanche
(0xd07369fae4a5bb13c9ce446b052c7867b1abdf6e). My API token is in the
ENVIO_API_TOKEN environment variable. Chart deposits per day by asset, priced in USD.
```
