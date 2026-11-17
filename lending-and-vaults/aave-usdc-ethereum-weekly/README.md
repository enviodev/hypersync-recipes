# Weekly USDC deposits and borrows on Aave V3 Ethereum

Reads every USDC `Supply`, `Withdraw`, `Borrow` and `Repay` event on the Aave V3 Ethereum Pool with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then adds them up by week.

These are the numbers behind Envio's post on the biggest week of USDC deposits on Aave in a year.

## Run it

You need Python 3.9 or newer and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py        # last 52 weeks
python script.py 26     # last 26 weeks
```

A year of events (about 619k) takes a couple of minutes.

## What it prints

```
Aave V3 Ethereum, USDC, 619,084 events, weeks ending 12 Nov 2026 12:22 UTC
Top 5 weeks by net deposits:
  week to 12 Nov 2026   deposits   +549.3M   borrows   +525.2M
  week to 29 Jan 2026   deposits   +253.1M   borrows   +315.2M
  week to 20 Nov 2025   deposits   +204.3M   borrows    +78.3M
  week to 14 May 2026   deposits   +166.8M   borrows   +162.8M
  week to 25 Dec 2025   deposits   +146.5M   borrows     -0.5M
Latest week: +549.3M deposited, +525.2M borrowed (96% of the new deposits)
```

That run was on 12th Nov 2026. Weeks are 7-day windows ending at the latest block, so the numbers shift a little with each run.

## How it counts

- The Pool address `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2` and USDC `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` come from Aave's [address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Ethereum.sol).
- The query asks for the four events with USDC as the reserve (topic1). It uses HyperSync's default join, and the script only keeps logs whose address, topic0 and reserve match.
- Net deposits are `Supply` minus `Withdraw`. Net borrows are `Borrow` minus `Repay`. Liquidations are not included, and interest is not counted.
- Checked over RPC: from block 26,348,515 to 26,398,743 (5 to 12 Nov, 12:04 UTC), aUSDC `totalSupply()` rose by 549.7M and variableDebtUSDC `totalSupply()` rose by 526.4M. The events give 549.1M and 525.5M for the same blocks. The gap is accrued interest.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Ethereum (endpoint
https://eth.hypersync.xyz) to read every Supply, Withdraw, Borrow and Repay event for USDC on the
Aave V3 Pool 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 for the last year. My API token is in the
ENVIO_API_TOKEN environment variable. Bucket them into weeks and show net deposits and net borrows
per week.
```
