# Every fixed-rate loan on Morpho Midnight

Up to 11 Nov 2026, **$102.3M had been borrowed on Morpho Midnight across 10K loans**, from 2.6K borrowing wallets and 495 lenders on five chains. Ethereum carried $87.4M of it and Base $14.9M. Borrowers mostly posted bitcoin ($57.6M) or ETH ($35.8M) as collateral, and the dollar-weighted average term was 51 days.

| By collateral | Borrowed | Share |
| --- | --- | --- |
| Bitcoin | $57,578,783 | 56.3% |
| ETH | $35,804,604 | 35.0% |
| Other | $7,100,249 | 6.9% |
| Not posted by the borrower | $1,838,734 | 1.8% |

| By term | Borrowed | Share |
| --- | --- | --- |
| Up to a week | $1,892,321 | 1.8% |
| 1 week to 1 month | $16,809,436 | 16.4% |
| 1 to 3 months | $81,183,740 | 79.3% |
| Over 3 months | $2,436,873 | 2.4% |

## Why it's interesting

[Morpho Midnight](https://docs.morpho.org/learn/concepts/midnight) is Morpho's fixed-rate lending protocol, where lenders and borrowers trade units that settle at a set maturity. There's no single "loan opened" event. A `Take` can close old debt, move credit between lenders or open new debt, so you have to replay every position to know which trades were real loans. This script does that replay on all five chains, which makes it a good template for any protocol where the meaning of an event depends on state.

## What it pulls

- Every `MarketCreated`, `Take`, `UpdatePosition`, `Withdraw`, `Repay`, `Liquidate` and `SupplyCollateral` log from the Midnight contract on each chain, with addresses from Morpho's [addresses page](https://docs.morpho.org/developers/contracts/addresses) and event layouts from [`EventsLib.sol`](https://github.com/morpho-org/midnight/blob/main/src/libraries/EventsLib.sol).
  - Ethereum [`0x471686c42792F93528B000beF54bC10E3aa2045f`](https://etherscan.io/address/0x471686c42792F93528B000beF54bC10E3aa2045f)
  - Base [`0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A`](https://basescan.org/address/0xAdedD8ab6dE832766Fedf0FaC4992E5C4D3EA18A)
  - Arc, Robinhood Chain and Tempo, in `MIDNIGHT`
- `AnswerUpdated` logs from Chainlink's ETH/USD aggregator on Ethereum (`0x7d4E742018fb52E48b08BE73d041C18B21de6Fb5`), to price WETH loans at the time they were taken.
- Token symbols and decimals, read once per token over each chain's public RPC.

In a `Take`, the buyer lends and the seller borrows. Units first close the buyer's debt and the seller's credit, the same way [`Midnight.sol`](https://github.com/morpho-org/midnight/blob/main/src/Midnight.sol) does, and whatever is left becomes new debt for the seller. Each piece of new debt is one loan, valued at the cash the borrower received. Dollar stablecoins (USDC, USDT, PYUSD, USDS, USDG, OUSD) count at $1. Bitcoin is cbBTC, WBTC and cirBTC, and ETH is WETH, weETH, wstETH, cbETH, rETH, savETH and their collateral wrappers. Test tokens and a handful of tiny loans in other tokens are left out and listed at the end of the output.

Every event, and the ETH price, comes from HyperSync. The ETH price is Chainlink's onchain feed, read as logs.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py               # every loan so far
python3 script.py 1794355200    # loans before 11 Nov 2026 00:00 UTC, the window above
```

Base has the most events, so a full run takes a few minutes. Sample output from the window above.

```
Ethereum: 3,096 Midnight events up to block 26,391,184, 1,615 markets
Base: 51,214 Midnight events up to block 56,019,515, 1,303 markets
Arc: 109 Midnight events up to block 30,677,938, 14 markets
Robinhood: 206 Midnight events up to block 111,644,508, 49 markets
Tempo: 73 Midnight events up to block 48,495,699, 7 markets

Borrowed on Morpho Midnight: $102,322,370 across 10,005 loans (first 2026-07-08, last 2026-11-10 23:34 UTC)
  2,623 borrowing wallets, 495 lending wallets

By chain
  Ethereum                     $    87,411,910   85.4%
  Base                         $    14,910,421   14.6%
  ...

By month
  2026-10                      $    71,586,858   70.0%
  2026-11                      $    22,670,706   22.2%
  2026-08                      $     3,805,807    3.7%
  2026-09                      $     2,942,269    2.9%
  2026-07                      $     1,316,728    1.3%

  dollar-weighted average term: 51 days
  left out: Arc EURC x1, Arc MXNB x1, Base EURC x3, Base TESTUSD x145, Base Zuzalu x1, Base cbBTC x13, Base dUSDC x3, Robinhood SPCX x16, Tempo TESTUSD x14

RPC check on Ethereum: replayed debt matches position() for 74 of 74 open borrows
```

Without a timestamp your numbers will be higher, as new loans come in.

## Change the window or chain

- **Window.** Pass a unix timestamp to count only loans taken before it.
- **Chains.** Each chain is one entry in `MIDNIGHT`, with its HyperSync slug, the Midnight address and a public RPC. Add a chain from Morpho's [addresses page](https://docs.morpho.org/developers/contracts/addresses) if it's on the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks).
- **Groups.** Edit `USD_STABLES`, `BTC` and `ETH` to change how tokens are valued and grouped.

## Check the numbers

- **Replay.** Every `Take` emits a `totalUnitsDelta`, and the replay matches it on every trade.
- **Positions.** As the RPC comparison, the final debt of every open Ethereum borrow matches Midnight's own `position()`, 74 of 74.
- **Morpho's own figure.** As an outside comparison, Morpho reported $102.7M in loans originated at 15:04 UTC on 10 Nov. Up to that minute, the replay counts $102.8M at the face value borrowers owe at maturity, or $102.2M in cash lent.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every Morpho Midnight
event on five chains, replay each position and find the trades that opened new
debt. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a weekly table of dollars borrowed, split by the market's maturity date, and
a list of the 20 markets with the most borrowed. Keep the standard library only.
Then pick three open borrows on Base and check the replayed debt against
position() on Midnight at the latest block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Morpho Midnight docs](https://docs.morpho.org/learn/concepts/midnight)
- [Midnight source](https://github.com/morpho-org/midnight)
- [Envio Discord](https://discord.gg/envio)
