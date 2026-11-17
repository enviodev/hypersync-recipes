# Weekly USDC deposits and borrows on Aave v3 Ethereum

In the week to 12 Nov 2026, **net USDC deposits on Aave v3 Ethereum were +$549.3M and net borrows were +$525.2M**. That was the biggest week for USDC deposits in the past year, more than twice the next one ($253.1M in the week to 29 Jan 2026).

| Week to | Net deposits | Net borrows |
| --- | --- | --- |
| 12 Nov 2026 | +549.3M | +525.2M |
| 29 Jan 2026 | +253.1M | +315.2M |
| 20 Nov 2025 | +204.3M | +78.3M |
| 14 May 2026 | +166.8M | +162.8M |
| 25 Dec 2025 | +146.5M | -0.5M |

## Why it's interesting

Aave's USDC market on Ethereum is where a lot of onchain dollar lending happens, so weekly flows there are a quick read on demand for dollars. Deposits and borrows moving together in the same week, as they did here, means the new USDC was put to work almost straight away. The script turns a year of events into that weekly view in a couple of minutes.

## What it pulls

- `Supply`, `Withdraw`, `Borrow` and `Repay` logs on the Aave v3 Ethereum Pool [`0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`](https://etherscan.io/address/0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2) where the reserve (topic1) is USDC [`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`](https://etherscan.io/address/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48). Both addresses are from Aave's [address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Ethereum.sol).
- Net deposits are `Supply` minus `Withdraw`, and net borrows are `Borrow` minus `Repay`. Liquidations and interest aren't counted.

Every number here comes from HyperSync.

## Run it

You need Python 3.9 or newer and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py        # last 52 weeks
python3 script.py 26     # last 26 weeks
```

A year of events (about 619K) takes a couple of minutes. Sample output from a run on 12 Nov 2026.

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

Weeks are 7-day windows ending at the latest block, so your numbers will shift a little with each run.

## Change the window or chain

- **Window.** The argument is the number of weeks. The query starts at `START` (block 23,780,000, about 12 Nov 2025), so move it back if you ask for more than 52 weeks.
- **Asset.** Change `USDC` to another reserve's address, padded to 32 bytes as a topic, and change the `1e6` where amounts are decoded if it has different decimals.
- **Chain.** Aave v3 runs on many chains. Change `HS` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `POOL` and `USDC` to the addresses in the matching file in the [address book](https://github.com/bgd-labs/aave-address-book/tree/main/src).

## Check the numbers

As the comparison over RPC, from block 26,348,515 to 26,398,743 (5 to 12 Nov, 12:04 UTC) aUSDC `totalSupply()` rose by 549.7M and variableDebtUSDC `totalSupply()` rose by 526.4M. The events give 549.1M and 525.5M for the same blocks, and the gap is accrued interest.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every USDC Supply,
Withdraw, Borrow and Repay on the Aave v3 Ethereum Pool and add them up by week.
My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add USDT and WETH as extra reserves, using the addresses in
https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Ethereum.sol,
and print one weekly table per reserve. Keep the standard library only. Then check
the latest week for USDT against the change in its aToken totalSupply() over the
same blocks.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Aave v3 docs](https://aave.com/docs)
- [Aave address book for Ethereum](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Ethereum.sol)
- [Envio Discord](https://discord.gg/envio)
