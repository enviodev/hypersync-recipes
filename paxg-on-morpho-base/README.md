# Borrowing against gold on Base (PAXG on Morpho)

Reads every Morpho market on Base that takes Paxos Gold (PAXG) as collateral with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), then every collateral deposit, withdrawal, borrow, repay, lender supply and liquidation in those markets. It also counts every PAXG mint and burn on Base.

These are the numbers behind Envio's post on borrowing USDC against gold on Base.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Add a Base block number to rerun a past snapshot exactly. The post used block 55,205,406:

```bash
python script.py 55205406
```

## What it prints

```
Market 0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392
  created 2026-10-27 (block 53,158,097), loan USDC, LLTV 77%, oracle 0x6a47f48780eaeb07ee18ca47a9c33c925961bfad
  PAXG collateral: 11.8555 now (12.3686 in, 0.5131 out, 0.0000 seized) ~ $48,785 at $4,115 per PAXG
  USDC borrowed: 22,272.99 in total, 1,214.67 repaid, 21,071.58 owed now with interest (RPC)
  USDC supplied by lenders now: 23,290.61  (90% lent out)
  35 unique borrowers, 24 wallets with collateral now, 0 liquidations, 774 events

Biggest market by collateral: 0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392
  median PAXG per wallet with collateral: 0.0307, biggest: 10.0606 (85% of the market)
  biggest borrower took 17,841.40 USDC (80% of all borrows), median borrower 41.80 USDC

PAXG on Base: 406.3339 from 262 mints and 276 burns (totalSupply() says 406.3339), first mint 2026-09-08
Share of all PAXG on Base sitting as Morpho collateral: 2.9%
```

It also prints the 3 smaller PAXG markets and the biggest market's collateral and borrowed USDC at the end of each UTC day. The numbers move as people borrow and repay, so a run without a block number will differ a little.

## How it counts

- Morpho's Base address comes from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses) (`0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb`), and PAXG's Base address from the [Paxos docs](https://docs.paxos.com/guides/stablecoin/paxg/mainnet) (`0xe904AEA5E1b110c9174728fA2efFc8aeD19E98Ef`, 18 decimals). One PAXG is one fine troy ounce of gold.
- Markets are found from every `CreateMarket` event on Morpho whose collateral token is PAXG. The [Morpho API](https://api.morpho.org/graphql) lists the same 4 markets, and the one with the activity (`0x48dca3ed...e392`) is supplied by Steakhouse USDC vaults.
- Collateral is `SupplyCollateral` minus `WithdrawCollateral` minus collateral seized in `Liquidate`. A borrower is any `onBehalf` address in a `Borrow` event.
- "Owed now" is the market's `totalBorrowAssets` from Base's public RPC, so it includes interest. Collateral from the events matches the Morpho API's `collateralAssets` to the last unit.
- The dollar value uses the market's own oracle `price()`. It's a guide, not a trading price.
- PAXG supply on Base is mints (Transfers from the zero address) minus burns (Transfers to it), and matches `totalSupply()` exactly.

## Learn more

- [Base on Envio](https://envio.dev/chains/base): HyperSync and HyperIndex support for Base
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview): turn these events into a live indexer with a GraphQL API
- [Dynamic contracts](https://docs.envio.dev/docs/HyperIndex/dynamic-contracts): track markets as they are created
- [Liqo](https://docs.envio.dev/showcase/liqo): a lending liquidation tracker built on HyperIndex that covers Morpho
- [USDG on Morpho](https://github.com/enviodev/hypersync-recipes/tree/main/usdg-on-morpho): a sister recipe for Paxos USDG markets on Morpho

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
SupplyCollateral, WithdrawCollateral, Borrow and Repay event on Morpho on Base
(0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb) for market
0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392 (PAXG collateral, USDC loans).
My API token is in the ENVIO_API_TOKEN environment variable.
Chart PAXG collateral and USDC borrowed at the end of each day.
```
