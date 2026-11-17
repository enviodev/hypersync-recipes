# MetaMask Money Account on Monad

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer for the vault behind MetaMask's Money Account on Monad. It follows every deposit, withdrawal and transfer of the vault's shares, so you get every wallet's balance, the day each wallet first deposited and new wallets per UTC day. It also follows the vault's share price and its supply position in Aave from their own events.

Up to Monad block 122,726,000 (16 Nov 2026, 11:16 UTC), **83,375 wallets had deposited since 2 Jun 2026, and about 800 new wallets made their first deposit each day** in the first half of November. From 2 to 15 Nov it was between 755 and 889 a day, 808 on average.

| Day (UTC) | New wallets |
| --- | ---: |
| 9 Nov 2026 | 768 |
| 10 Nov 2026 | 822 |
| 11 Nov 2026 | 755 |
| 12 Nov 2026 | 822 |
| 13 Nov 2026 | 881 |
| 14 Nov 2026 | 786 |
| 15 Nov 2026 | 788 |

At that block 69,374 wallets held vault shares, and 38,870 of them held at least $1. The vault had 60,044,007 shares, worth about 61.5M mUSD at the accountant's share price. It also supplied 56.0M of the 56.1M mUSD in Aave v3 on Monad. The indexer produces all of these, the share price from the accountant's events and the Aave figures from the aToken's events.

## Why it's interesting

Money Account is a savings product built into a wallet lots of people already use, and every deposit lands onchain as a vault share mint. That makes it a clean way to watch real consumer adoption on Monad, one wallet at a time.

The whole history, the vault's 404K share transfers plus the accountant's and the aToken's events since June, indexes in under a minute because Monad is on [HyperSync](https://docs.envio.dev/docs/HyperSync/overview).

## What it indexes and stores

It starts at block 78,633,433, the vault's first transfer, and listens to three contracts.

- The vault share `Transfer(address indexed from, address indexed to, uint256 amount)`. A mint (a transfer from the zero address) is a deposit and a burn is a withdrawal.
- The accountant's `ExchangeRateUpdated(uint256 newRate)`, which it emits with the new share price on every deposit and rate update. The latest one is the share price.
- The aMonmUSD aToken's `Mint`, `Burn` and `BalanceTransfer`. Each carries Aave's liquidity index, so the handler rebuilds scaled balances, and the scaled balance times the latest index is the balance in mUSD.

| Contract | Address |
| --- | --- |
| Money Account vault (Veda BoringVault, "mUSD Vault", vmUSD) | [`0x1C8a336051D2024E318A229d01F9F6CF96efD316`](https://monadscan.com/address/0x1C8a336051D2024E318A229d01F9F6CF96efD316) |
| Accountant (share price) | [`0x98A45D90E81849a5743241d3ff765F9Fd788206a`](https://monadscan.com/address/0x98A45D90E81849a5743241d3ff765F9Fd788206a) |
| mUSD | [`0xacA92E438df0B2401fF60dA7E4337B687a2435DA`](https://monadscan.com/address/0xacA92E438df0B2401fF60dA7E4337B687a2435DA) |
| Aave v3 aMonmUSD | [`0xDBb2e1b6BC94328Df2662A1796AB6A23fCde3199`](https://monadscan.com/address/0xDBb2e1b6BC94328Df2662A1796AB6A23fCde3199) |

The vault, accountant and mUSD addresses are MetaMask's own `moneyAccountVaultConfig` in the [MetaMask extension repo](https://github.com/MetaMask/metamask-extension/blob/main/test/e2e/feature-flags/feature-flag-registry.ts). Monad lists the same vault as `MoneyAccountVault` in its [protocols registry](https://github.com/monad-crypto/protocols/blob/main/mainnet/metamask.jsonc). The aToken comes from the [Aave address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol). Steakhouse Financial curates the vault and Veda built it ([Steakhouse](https://kitchen.steakhouse.financial/p/the-metamask-money-account), [MetaMask](https://metamask.com/news/introducing-metamask-money-account)).

The handlers are [`src/handlers/MoneyAccountVault.ts`](src/handlers/MoneyAccountVault.ts) and [`src/handlers/Pricing.ts`](src/handlers/Pricing.ts). They keep five entities.

- **`Holder`** has one row per wallet, with its share balance, the UTC day and block of its first deposit, and its number of deposits.
- **`DailyStat`** has one row per UTC day, with new wallets, deposits, shares minted and shares burned.
- **`Totals`** is one row with id `monad`, holding wallets that ever deposited, current holders, share supply, deposits, withdrawals and the last block seen.
- **`SharePrice`** is one row with the latest share price in mUSD and its block.
- **`AavePosition`** is one row with the vault's scaled aMonmUSD balance, the scaled supply of every holder and the latest liquidity index.

Shares, mUSD and aMonmUSD have 6 decimals. The liquidity index has 27.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
git clone https://github.com/enviodev/hypersync-use-cases.git
cd hypersync-use-cases/metamask-money-account
cp .env.example .env   # then paste your token into ENVIO_API_TOKEN
pnpm install
pnpm codegen
pnpm dev
```

The GraphQL playground is at http://localhost:8080 (local admin secret `testing`).

```graphql
{
  Totals { wallets holders shareSupply deposits withdrawals lastBlock }
  DailyStat(order_by: { id: desc }, limit: 14) { id newWallets deposits }
  Holder(where: { balance: { _gte: "975546" } }, limit: 10) { id balance firstDepositDay }
  SharePrice { rate block }
  AavePosition { vaultScaled totalScaled liquidityIndex block }
}
```

975,546 shares was $1 at the share price on 16 Nov 2026 (1.025068 mUSD per share). The current price is `rate` in `SharePrice`. For the Aave balance in mUSD, multiply a scaled figure by `liquidityIndex` and divide by 10^27.

To run the whole history in memory, with no Docker or Postgres, and write `out/summary.json` and `out/holders.json`, use the full-run script. The summary includes the vault's value at the share price, the holders with at least $1 and the Aave figures. It also needs `ENVIO_API_TOKEN` in `.env`.

```bash
pnpm full-run                      # stops at block 122,726,000
END_BLOCK=123000000 pnpm full-run  # or pick your own block
```

### Make it live

There's no `end_block` in `config.yaml`, so `pnpm dev` backfills and then keeps following Monad's head. To index only part of the history, set `start_block` and add `end_block` under the chain in `config.yaml`.

### Deploy it

Push your fork to GitHub and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service) to get a hosted GraphQL endpoint that stays in sync with Monad.

## Check the numbers

These are the checks we ran at block 122,726,000. The RPC reads and Aave's API are outside sources, used here only as the comparison.

- **Balances.** A separate HyperSync script pulled all 403,875 vault `Transfer` logs to that block and rebuilt every balance. Its 69,374 non-zero balances match the indexer's wallet by wallet. Their sum, 60,044,007.367598 shares, equals the vault's `totalSupply()` read over public Monad RPC at that block.
- **Holders.** We read `balanceOf` over public RPC at the same block for 20 randomly picked holders. All 20 matched to the last unit, and wallets the indexer shows as fully withdrawn returned 0.
- **New wallets.** For 15 Nov 2026 we pulled every vault mint from public RPC with `eth_getLogs` in 100-block chunks (blocks 122,308,133 to 122,592,638). It returned the same 1,893 mints to the same recipients as HyperSync, and 788 of those wallets had never deposited before, the same as the indexer.
- **Share price.** The indexer's price, from the accountant's last event at block 122,725,997, is 1.025068 mUSD per share. RPC `getRate()` on the accountant returned the same 1.025068 at block 122,726,000.
- **Aave.** The indexer gives the vault 56,009,235 aMonmUSD out of 56,092,741, using the liquidity index from the aToken's last event at block 122,724,590. RPC `balanceOf` on aMonmUSD gave 56,009,253 for the vault against a `totalSupply` of 56,092,759 at block 122,726,000. The 18 mUSD gap is interest accrued in the 1,410 blocks after that last event, which RPC includes and the event index doesn't yet. Aave's own API reported a 56.10M mUSD reserve on Monad and a 56.01M supply position for the vault.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
This is an Envio HyperIndex indexer for MetaMask's Money Account vault on Monad
(chain 143). Read README.md, config.yaml, schema.graphql and
src/handlers/MoneyAccountVault.ts, then the HyperIndex docs at
https://docs.envio.dev/docs/HyperIndex/overview. My API token is in the
ENVIO_API_TOKEN environment variable.

Add a weekly rollup next to DailyStat with new wallets, deposits, withdrawals
and net shares minted per ISO week (Monday 00:00 UTC). Run `pnpm codegen`, then
`END_BLOCK=122726000 pnpm full-run`, and check that the weekly new wallets add
up to the 83,375 wallets in Totals.
```

## Links

- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview)
- [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [MetaMask Money Account](https://support.metamask.io/trade/money-account/)
- [Envio Discord](https://discord.gg/envio)
