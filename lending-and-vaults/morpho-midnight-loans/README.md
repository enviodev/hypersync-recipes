# Every fixed-rate loan on Morpho Midnight

Reads every market, trade, repayment, withdrawal, liquidation and collateral deposit on [Morpho Midnight](https://docs.morpho.org/learn/concepts/midnight), Morpho's fixed-rate lending protocol, on all five chains it runs on, with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It replays every position to find the trades that opened new debt, prices each loan in dollars, and splits the total by chain, by the collateral the borrower posted and by loan term.

These are the numbers behind Envio's post on Morpho Midnight passing $100M in loans.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Add a unix timestamp to count only loans taken before it. The post used 11th November 2026, 00:00 UTC:

```bash
python script.py 1794355200
```

Base has the most events, so a full run takes a few minutes.

## What it prints

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
  Robinhood                    $            35    0.0%
  Arc                          $             3    0.0%
  Tempo                        $             0    0.0%

By collateral the borrower posted
  Bitcoin                      $    57,578,783   56.3%
  ETH                          $    35,804,604   35.0%
  Other                        $     7,100,249    6.9%
  Not posted by the borrower   $     1,838,734    1.8%

By time from loan to maturity
  1 to 3 months                $    81,183,740   79.3%
  1 week to 1 month            $    16,809,436   16.4%
  over 3 months                $     2,436,873    2.4%
  up to a week                 $     1,892,321    1.8%

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

Morpho reported $102.7M in loans originated at 15:04 UTC on 10th November. Up to that minute, this replay counts $102.8M at the face value borrowers owe at maturity, or $102.2M in cash lent, so the two line up.

## How it counts

- Midnight contract addresses come from Morpho's [addresses page](https://docs.morpho.org/developers/contracts/addresses) and event layouts from [`EventsLib.sol`](https://github.com/morpho-org/midnight/blob/main/src/libraries/EventsLib.sol).
- In a `Take`, the buyer lends and the seller borrows. Units first close the buyer's debt and the seller's credit, the same way [`Midnight.sol`](https://github.com/morpho-org/midnight/blob/main/src/Midnight.sol) does, and whatever is left becomes new debt for the seller. Each piece of new debt is one loan, valued at the cash the borrower received for it. Lenders selling their credit to other lenders and borrowers closing debt early are not loans.
- The replay is checked against the `totalUnitsDelta` every `Take` emits, and the final debt of every open Ethereum borrow is checked against Midnight's own `position()` over RPC.
- Dollar stablecoins (USDC, PYUSD, USDS, USDG, OUSD) count at $1. WETH loans are priced with Chainlink's ETH/USD feed at the time of the loan. Test tokens, Dummy USD Coin and a handful of tiny loans in other tokens are left out and listed at the end.
- Collateral is what the borrower deposited in that market. Bitcoin is cbBTC and WBTC. ETH is WETH, weETH, wstETH, cbETH, rETH and wrapped staked ETH. Loans where the borrower's own address posted no collateral (for example, when a helper contract posted it) are counted separately.
- Loan term is the time from the loan to the market's maturity.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every Take event from
Morpho Midnight (https://github.com/morpho-org/midnight) on Ethereum and Base. My API token is in the
ENVIO_API_TOKEN environment variable. Replay each position to find the trades that opened new debt,
then show me the dollars borrowed each week, split by the loan's maturity date.
```
