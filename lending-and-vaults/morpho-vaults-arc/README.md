# Morpho vaults on Arc

Up to Arc block 30,839,502, **1.7K wallets had put $173.6M of USDC, net of withdrawals, into Morpho vaults on Arc**, across 7.9K deposits into 39 vaults. Most of it is lent against cirBTC, Circle's wrapped bitcoin. 329 wallets have borrowed in the two USDC/cirBTC markets, with $155.6M of principal outstanding, and 84% of the USDC in the vaults sits in those two markets.

| | Up to block 30,839,502 |
| --- | --- |
| Vaults created through VaultV2Factory | 75 (52 in USDC) |
| USDC deposits | 7,882 from 1,658 wallets |
| USDC deposited, net of withdrawals | $173,560,644 |
| USDC/cirBTC borrowers | 329 |
| USDC/cirBTC principal outstanding | $155,622,772 |

## Why it's interesting

Arc is Circle's own chain, and Morpho vaults are one of the first places its USDC goes to earn. A vault takes deposits and lends them out to Morpho markets through adapters, so following the money means joining vault events, market events and the adapters in between. This script does all three, which makes it a good template for tracing any vault's deposits to the loans behind them.

## What it pulls

- `CreateVaultV2` logs from Morpho's VaultV2Factory on Arc, `0x3b0eefaBfa22ec7CF2c73877ac16e78D76749f12`, then `Deposit` and `Withdraw` logs from every vault it created.
- `CreateMarket`, `Supply`, `Borrow` and `Repay` logs on Morpho on Arc, `0x34CD04070dD72b14E241112F6d83812Df5Af7fCD`, for the USDC/cirBTC markets. Both addresses are from the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses).
- USDC on Arc is `0x3600000000000000000000000000000000000000` (6 decimals through its ERC-20 interface) and cirBTC is `0x171A4217b86A807A64eB94757Db6849fb4bDbAA0` (8 decimals), from the [Arc contract addresses page](https://docs.arc.io/arc/references/contract-addresses).

A depositor is any `onBehalf` address in a vault `Deposit` event. Vault totals are deposits minus withdrawals, and only USDC vaults are summed. Arc also has smaller vaults in EURC, MXNB, GBPA and wARS.

Wallets, deposits, net deposits, borrowers and principal outstanding come from HyperSync. The 84% share, the vault names and the per-vault sizes in the output are read over Arc's public RPC. To get the share, the script finds every address that supplied to the USDC/cirBTC markets, keeps the ones whose `parentVault()` is a USDC vault, and reads each one's `position()` on Morpho, then divides by the vaults' `totalAssets()`.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py              # up to the latest block
python3 script.py 30839502     # up to the block used above
```

A full run takes a few minutes, mostly the RPC calls at the end. Sample output from the block above.

```
Morpho vaults on Arc, up to block 30,839,502
  75 vaults created through VaultV2Factory, 52 of them USDC vaults
  7,882 USDC deposits from 1,658 wallets into 39 vaults
  USDC deposited, net of withdrawals: $173,560,644
  USDC in the vaults now, from totalAssets() over RPC: $174,083,432
  biggest USDC vaults (RPC totalAssets, depositor wallets)
    Galaxy USDC                  $    92,633,842    807 wallets  0x8e357432cc12ff425c36432f312968aeb16112af
    Keyrock Prime USDC           $    75,231,468    298 wallets  0x5befab92a5a3d60f578cb51eeb4e4fd50a1e3123
    Steakhouse Prime USDC        $     5,287,038    205 wallets  0xbeef0016cb2fd5c352ea7ca08a9f54739dfa7298
    ...
  USDC in the vaults at the end of each day (deposits minus withdrawals)
    2026-09-15      +74,500,025  ->  $    74,500,095
    2026-09-16      +76,393,667  ->  $   150,893,762
    ...

USDC lent against cirBTC on Morpho on Arc
  2 USDC/cirBTC markets, 329 wallets have borrowed
  principal outstanding from events: $155,622,772
  owed now, totalBorrowAssets over RPC: $156,165,257 of $171,610,260 supplied (91% lent out)
  vault USDC supplied to the USDC/cirBTC markets: $146,525,227 (84% of the $174,083,432 in the vaults)
```

Without a block number your numbers will differ a little.

## Change the window or chain

- **Block.** Pass an Arc block number to rebuild everything as it stood then.
- **Asset.** Swap `USDC` for EURC or another vault asset to size those vaults instead, and `CIRBTC` for another collateral to follow a different set of markets.
- **Chain.** Morpho vaults run on many chains. Change `HYPERSYNC` to that chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks), `RPC` to a public RPC there, and `MORPHO` and `VAULT_FACTORY` to the addresses in the [Morpho docs](https://docs.morpho.org/get-started/resources/addresses).

## Check the numbers

The script checks itself against Arc's public RPC as the comparison. Net deposits from events ($173.6M) sit just below the vaults' own `totalAssets()` ($174.1M), and principal from events ($155.6M) sits just below `totalBorrowAssets` ($156.2M). In both cases the gap is interest.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to find every Morpho vault on Arc,
read every deposit and withdrawal, and follow vault USDC into the USDC/cirBTC
markets. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Add a daily series per vault of USDC held (deposits minus withdrawals) and new
depositor wallets, and write it to a CSV. Keep the standard library only. Then
check the last row for the biggest vault against its totalAssets() on
https://rpc.mainnet.arc.io at the same block.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Morpho addresses](https://docs.morpho.org/get-started/resources/addresses)
- [Arc contract addresses](https://docs.arc.io/arc/references/contract-addresses)
- [Envio Discord](https://discord.gg/envio)
