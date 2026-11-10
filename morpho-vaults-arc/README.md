# Morpho vaults on Arc

Morpho vaults on Arc, Circle's L1, hold about $161M of USDC, and most of it is lent out against cirBTC, Circle's wrapped bitcoin. This script reads every vault created by Morpho's vault factory on Arc, every deposit and withdrawal in those vaults, and every borrow and repay in the USDC/cirBTC markets on Morpho, all with [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview). It then checks the vault totals against each vault's own `totalAssets()` over RPC.

These are the numbers behind Envio's post on Morpho vaults on Arc.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py
```

Add an Arc block number to rerun a past snapshot exactly. The post used block 30,581,168:

```bash
python script.py 30581168
```

A full run takes a minute or two. Most of that is the RPC calls at the end.

## What it prints

```
Morpho vaults on Arc, up to block 30,581,168
  74 vaults created through VaultV2Factory, 52 of them USDC vaults
  7,657 USDC deposits from 1,616 wallets into 39 vaults
  USDC deposited, net of withdrawals: $160,913,052
  USDC in the vaults now, from totalAssets() over RPC: $161,415,356
  biggest USDC vaults (RPC totalAssets, depositor wallets)
    Galaxy USDC                  $    80,029,562    790 wallets  0x8e357432cc12ff425c36432f312968aeb16112af
    Keyrock Prime USDC           $    75,222,145    282 wallets  0x5befab92a5a3d60f578cb51eeb4e4fd50a1e3123
    Steakhouse Prime USDC        $     5,290,468    203 wallets  0xbeef0016cb2fd5c352ea7ca08a9f54739dfa7298
    ...
  USDC in the vaults at the end of each day (deposits minus withdrawals)
    2026-09-15      +74,500,025  ->  $    74,500,095
    2026-09-16      +76,393,667  ->  $   150,893,762
    ...

USDC lent against cirBTC on Morpho on Arc
  2 USDC/cirBTC markets, 328 wallets have borrowed
  principal outstanding from events: $158,612,960
  owed now, totalBorrowAssets over RPC: $159,131,727 of $174,867,277 supplied (91% lent out)
```

The numbers move as people deposit, borrow and repay, so a run without a block number will differ a little.

## How it counts

- The Morpho addresses on Arc come from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses): Morpho `0x34CD04070dD72b14E241112F6d83812Df5Af7fCD` and VaultV2Factory `0x3b0eefaBfa22ec7CF2c73877ac16e78D76749f12`. Every vault in the script comes from a `CreateVaultV2` event on that factory.
- USDC on Arc is `0x3600000000000000000000000000000000000000`, read with 6 decimals through its ERC-20 interface. cirBTC is `0x171A4217b86A807A64eB94757Db6849fb4bDbAA0` (8 decimals).
- Each HyperSync query asks for one set of contracts and event signatures, and the script keeps only logs whose address and topic0 both match.
- A depositor is any `onBehalf` address in a vault `Deposit` event. Vault totals are deposits minus withdrawals. The RPC `totalAssets()` figure is a little higher because it includes the interest the vaults have earned.
- The cirBTC side covers the two USDC/cirBTC markets, both with an 86% LLTV. "Principal outstanding" is borrows minus repays from events. "Owed now" is each market's `totalBorrowAssets` over RPC, so it includes interest. The two agree to within about $0.5M.
- Only USDC vaults are summed. Arc also has smaller vaults in EURC, MXNB, GBPA and wARS.

## Learn more

- [Arc on Envio](https://envio.dev/chains/arc): HyperSync and HyperRPC support for Arc
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview): how the queries in this script work
- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview): turn these events into a live indexer with a GraphQL API
- [Coinbase borrowing on Morpho, Base](https://github.com/enviodev/hypersync-recipes/tree/main/coinbase-borrow-morpho-base): the same approach for Morpho markets on Base
- [USDC mints and burns on Arc](https://github.com/enviodev/hypersync-recipes/tree/main/arc-usdc-mint-burn): USDC supply on Arc

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) on Arc
(https://arc.hypersync.xyz) to read every CreateVaultV2 event from Morpho's
VaultV2Factory (0x3b0eefaBfa22ec7CF2c73877ac16e78D76749f12), then every Deposit
and Withdraw event from those vaults. My API token is in the ENVIO_API_TOKEN
environment variable. Chart USDC held in each vault per day since the first deposit.
```
