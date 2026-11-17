# Borrowing USDC against gold on Base

Up to Base block 58,686,017 on 17 Nov 2026, **78 borrowers had taken 202.9K USDC against Paxos Gold (PAXG) on Morpho on Base, with 133.98 PAXG (about $517K at $3,861.79 per PAXG) posted as collateral and no liquidations**. With interest, 197.4K USDC was still owed. Almost all of it is in one market, created on 27 Oct 2026 with a 77% LLTV. PAXG on Base had grown to 609.76 PAXG since its first mint on 8 Sep 2026, and 22.0% of it was working as Morpho collateral.

## Why it's interesting

Gold you can borrow against onchain is a simple idea that's only recently got going on Base. This script tracks the whole thing from Morpho's events, from finding the markets to every deposit, borrow, repay and liquidation in them. Because Morpho runs every market in one contract, the same pattern works for any collateral token you care about.

## What it pulls

- Every `CreateMarket` on Morpho on Base whose collateral is PAXG, then every `SupplyCollateral`, `WithdrawCollateral`, `Borrow`, `Repay`, `Supply`, `Withdraw`, `Liquidate` and `AccrueInterest` in those markets, from [HyperSync](https://docs.envio.dev/docs/HyperSync/overview). Collateral, total borrowed, borrower counts, liquidations, USDC owed and USDC supplied all come from HyperSync.
- Every PAXG mint and burn on Base, from HyperSync. PAXG supply on Base comes from here.
- `AnswerUpdated` logs from the Chainlink aggregator each market's oracle reads (XAU / USD for the active market, PAXG / USD for the oldest), from HyperSync. The dollar value of the collateral is the latest answer at or before the snapshot block. The active market's oracle reads gold per troy ounce, and one PAXG is one troy ounce.
- The market oracle's `price()` over Base's public RPC, as a labelled check on that price. RPC is also used for the other checks below.

Morpho on Base is [`0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb`](https://docs.morpho.org/get-started/resources/addresses) and PAXG on Base is [`0xe904AEA5E1b110c9174728fA2efFc8aeD19E98Ef`](https://docs.paxos.com/guides/stablecoin/paxg/mainnet), with 18 decimals. One PAXG is one fine troy ounce of gold.

Collateral is `SupplyCollateral` minus `WithdrawCollateral` minus collateral seized in `Liquidate`. USDC owed is `Borrow` minus `Repay`, minus debt repaid or written off in `Liquidate`, plus the interest in each `AccrueInterest`, which is how Morpho keeps `totalBorrowAssets`. USDC supplied works the same way from `Supply`, `Withdraw`, bad debt and interest. A borrower is any `onBehalf` address in a `Borrow` event. The active market (`0x48dca3ed...e392`) is supplied by Steakhouse USDC vaults.

## Run it

You need Python 3 (standard library only) and a free HyperSync API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py              # full history up to now
python3 script.py 58686017     # stop at the block used above
```

Sample output at block 58,686,017.

```
Market 0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392
  created 2026-10-27 (block 53,158,097), loan USDC, LLTV 77%, oracle 0x6a47f48780eaeb07ee18ca47a9c33c925961bfad
  PAXG collateral: 133.9770 now (137.0605 in, 3.0835 out, 0.0000 seized) ~ $517,391 at $3,861.79 per PAXG (Chainlink feed, HyperSync)
  Check (oracle price() over RPC): $3,861.79 per PAXG, gap +0.00%
  USDC borrowed: 202,863.65 in total, 5,614.47 repaid, 197,384.66 owed now with interest
  USDC supplied by lenders now: 220,674.50  (89% lent out)
  Check (RPC market()): 197,384.66 owed (gap -0.00), 220,674.50 supplied (gap 0.00)
  78 unique borrowers, 60 wallets with collateral now, 0 liquidations, 2153 events
...

PAXG on Base: 609.7627 from 341 mints and 297 burns, first mint 2026-09-08
  Check (RPC totalSupply()): 609.7627, gap -0.0000
Share of all PAXG on Base sitting as Morpho collateral: 22.0%
```

It also prints the three other PAXG markets and the main market's collateral and borrowed USDC at the end of each UTC day. Without a block number your numbers will differ a little.

## Change the window or chain

- **Block.** Pass a Base block number to stop there and rerun a past snapshot exactly. The PAXG price is the latest Chainlink answer at or before that block.
- **Another collateral.** Swap `PAXG` for any token's Base address to find every Morpho market that takes it as collateral, and add each market's oracle to `ORACLE_FEED` with the Chainlink aggregator it reads. The rest of the script stays the same.
- **Chain.** Morpho uses the same address on many chains. Swap `HYPERSYNC` for that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` for a public RPC there, and `PAXG` and `USDC` for that chain's addresses.

## Check the numbers

The script checks itself against Base's public RPC at the same block. It prints the oracle's own `price()` beside the Chainlink price it read with HyperSync for each market, and the two were identical in the run above. USDC owed and supplied, rebuilt from events, match Morpho's `market()` to the cent in all four markets, and PAXG supply rebuilt from mints and burns matches `totalSupply()` exactly. As an outside comparison, collateral from the events matches `collateralAssets` from the Morpho GraphQL API (`api.morpho.org/graphql`) to the last unit, and the API lists the same four PAXG markets.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every Morpho market on Base
that takes PAXG as collateral and read every collateral, borrow, repay, supply and
liquidation event in them. My HyperSync token is in the ENVIO_API_TOKEN environment
variable.

Point it at cbBTC on Base (0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf) instead of
PAXG and print the five largest markets by collateral. Keep the standard library only.
Then check one market's collateral total against collateralAssets in the Morpho API.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Base on Envio](https://envio.dev/chains/base)
- [Liqo, a liquidation tracker built on HyperIndex](https://docs.envio.dev/showcase/liqo)
- [Morpho docs](https://docs.morpho.org)
- [PAXG on Base](https://docs.paxos.com/guides/stablecoin/paxg/mainnet)
- [Envio Discord](https://discord.gg/envio)
