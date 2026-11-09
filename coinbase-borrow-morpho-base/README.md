# Coinbase borrowing on Morpho, Base

Coinbase's bitcoin-backed loans run through the cbBTC/USDC market on Morpho on Base, and its new gold-backed loans run through a PAXG/USDC market. This script reads every collateral deposit, withdrawal, borrow, repay and liquidation in both markets with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It rebuilds how much collateral each market holds, how many wallets have borrowed, and the collateral and outstanding USDC at the end of every month.

These are the numbers behind Envio's post on the market behind Coinbase loans.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Add a Base block number to rerun a past snapshot exactly. The post used block 55,212,962:

```bash
python script.py 55212962
```

The cbBTC market has more than 1.5 million events, so a full run takes a while.

## What it prints

```
cbBTC/USDC market 0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836 (oracle 0x663becd10dae6c4a3dcd89f1d76c1174199639b9), up to Base block 55,212,962
  collateral now: 40,602.5463 cbBTC ~ $3,029,058,806 at $74,602.68 per cbBTC
  USDC owed now: $1,623,913,618 (RPC, with interest); $3,757,272,323 borrowed in total since 2024-09-13
  75,465 unique borrowers, 1,550,996 collateral, borrow, repay and liquidation events
  end of each month: collateral, USDC principal outstanding (borrows minus repays)
    2024-09         16.8918 cbBTC  $         561,934
    ...
    2026-11     40,602.5463 cbBTC  $   1,539,700,362

PAXG/USDC market 0x48dca3ed245fb30931013a676d3451f7602b11150f92743ad93159628cbbe392 (oracle 0x6a47f48780eaeb07ee18ca47a9c33c925961bfad), up to Base block 55,212,962
  collateral now: 11.8555 PAXG ~ $48,785 at $4,114.98 per PAXG
  USDC owed now: $21,074 (RPC, with interest); $22,275 borrowed in total since 2026-10-27
  35 unique borrowers, 304 collateral, borrow, repay and liquidation events
```

The numbers move as people borrow and repay, so a run without a block number will differ a little.

## How it counts

- Morpho's Base address comes from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses) (`0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb`). The market ids come from the [Morpho API](https://api.morpho.org/graphql), and the script reads each market's tokens and oracle back from Morpho's `idToMarketParams` on chain.
- cbBTC on Base is `0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf` (8 decimals). PAXG on Base is `0xe904AEA5E1b110c9174728fA2efFc8aeD19E98Ef` (18 decimals), from the [Paxos docs](https://docs.paxos.com/guides/stablecoin/paxg/mainnet).
- Collateral is `SupplyCollateral` minus `WithdrawCollateral` minus collateral seized in `Liquidate`. At block 55,212,962 this matches the Morpho API's `collateralAssets` to within 0.05 cbBTC, the gap being blocks between the two reads.
- A borrower is any `onBehalf` address in a `Borrow` event. "Owed now" is the market's `totalBorrowAssets` from Base's public RPC, so it includes interest.
- Dollar values use each market's own oracle `price()`. They're a guide, not a trading price.
- The cbBTC/USDC market is open to anyone on Morpho, so its totals include every borrower in it, not only those who came through Coinbase.

## Learn more

- [Base on Envio](https://envio.dev/chains/base): HyperSync and HyperIndex support for Base
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview): turn these events into a live indexer with a GraphQL API
- [Liqo](https://docs.envio.dev/showcase/liqo): a lending liquidation tracker built on HyperIndex that covers Morpho
- [PAXG on Morpho, Base](https://github.com/enviodev/hypersync-recipes/tree/main/paxg-on-morpho-base): a deeper look at the gold market
- [USDG on Morpho](https://github.com/enviodev/hypersync-recipes/tree/main/usdg-on-morpho): Paxos USDG markets on Morpho

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every
SupplyCollateral, WithdrawCollateral, Borrow and Repay event on Morpho on Base
(0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb) for the cbBTC/USDC market
0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836.
My API token is in the ENVIO_API_TOKEN environment variable.
Chart new borrowers per week since the market opened.
```
