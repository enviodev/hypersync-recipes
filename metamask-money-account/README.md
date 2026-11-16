# MetaMask Money Account on Monad

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer for MetaMask's Money Account vault on Monad. It follows every deposit, withdrawal and transfer of the vault's shares, so you get every wallet's balance, the date each wallet first deposited and new wallets per UTC day.

Monad is on [HyperSync](https://docs.envio.dev/docs/HyperSync/overview), so the whole history (about 400K events since June) indexes in under a minute.

## Contracts

| Contract | Chain | Address |
|---|---|---|
| Money Account vault (Veda BoringVault, "mUSD Vault", vmUSD) | Monad (143) | `0x1C8a336051D2024E318A229d01F9F6CF96efD316` |
| Accountant (share price) | Monad (143) | `0x98A45D90E81849a5743241d3ff765F9Fd788206a` |
| mUSD | Monad (143) | `0xacA92E438df0B2401fF60dA7E4337B687a2435DA` |
| Aave v3 aMonmUSD | Monad (143) | `0xDBb2e1b6BC94328Df2662A1796AB6A23fCde3199` |

The vault, accountant and mUSD addresses are MetaMask's own `moneyAccountVaultConfig` in the [MetaMask extension repo](https://github.com/MetaMask/metamask-extension/blob/main/test/e2e/feature-flags/feature-flag-registry.ts). Monad lists the same vault as `MoneyAccountVault` in its [protocols registry](https://github.com/monad-crypto/protocols/blob/main/mainnet/metamask.jsonc). The aToken comes from the [Aave address book](https://github.com/bgd-labs/aave-address-book/blob/main/src/AaveV3Monad.sol). Steakhouse Financial curates the vault and Veda built it ([Steakhouse](https://kitchen.steakhouse.financial/p/the-metamask-money-account), [MetaMask](https://metamask.com/news/introducing-metamask-money-account)).

## The indexer

`config.yaml`:

```yaml
contracts:
  - name: MoneyAccountVault
    events:
      - event: Transfer(address indexed from, address indexed to, uint256 amount)
chains:
  - id: 143
    start_block: 78633433
    contracts:
      - name: MoneyAccountVault
        address: 0x1C8a336051D2024E318A229d01F9F6CF96efD316
```

The handler is [`src/handlers/MoneyAccountVault.ts`](src/handlers/MoneyAccountVault.ts). A deposit mints vault shares (a `Transfer` from the zero address) and a withdrawal burns them.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and an API token from the [Envio Dashboard](https://envio.dev/app/api-tokens).

```bash
cp .env.example .env   # then paste your token into it
pnpm install
pnpm codegen
pnpm dev
```

The GraphQL playground is at http://localhost:8080 (admin secret `testing`).

To run the whole history in memory without Postgres and write `out/summary.json`:

```bash
pnpm full-run                      # stops at block 122,726,000
END_BLOCK=123000000 pnpm full-run  # or pick your own block
```

## Deploy it on Envio Cloud

Push the folder to a GitHub repo and add it as an indexer in the [Envio Cloud dashboard](https://envio.dev/app). Envio Cloud backfills, follows Monad's head and gives you a hosted GraphQL endpoint. See [Hosted service deployment](https://docs.envio.dev/docs/HyperIndex/hosted-service-deployment).

## Query it

```graphql
{
  Totals { wallets holders shareSupply deposits withdrawals lastBlock }
  DailyStat(order_by: { id: desc }, limit: 14) { id newWallets deposits }
  Holder(where: { balance: { _gte: "975546" } }, limit: 10) { id balance firstDepositDay }
}
```

`975546` shares is $1 at the share price on 16 November (1.025068 mUSD per share). Read the live price with `getRate()` on the accountant.

## What we found

At Monad block 122,726,000 (16 November 2026, 11:16 UTC):

- **56.0M of the 56.1M mUSD supplied to Aave v3 on Monad comes from the vault.** RPC `balanceOf` on aMonmUSD gave 56,009,253 for the vault against a `totalSupply` of 56,092,759.
- **38,870 wallets hold at least $1** in the vault, out of 69,374 with any balance. 83,375 wallets have deposited since 2 June.
- **About 800 new wallets a day.** From 2 to 15 November, between 755 and 889 wallets made their first deposit each UTC day, 808 on average. On 15 November it was 788.
- The vault has 60,044,007 shares, worth about 61.5M mUSD.

| Day (UTC) | New wallets |
|---|---:|
| 9 Nov | 768 |
| 10 Nov | 822 |
| 11 Nov | 755 |
| 12 Nov | 822 |
| 13 Nov | 881 |
| 14 Nov | 786 |
| 15 Nov | 788 |

Your numbers will be higher, since the vault keeps growing.

## How we checked it

- **Balances.** A separate HyperSync script pulled all 403,875 vault `Transfer` logs to block 122,726,000 and rebuilt every balance. The indexer's 69,374 non-zero balances are identical to the script's, wallet by wallet. Their sum, 60,044,007.367598 shares, equals the vault's `totalSupply()` read over public Monad RPC (`rpc.monad.xyz`) at that block.
- **Holders.** We read `balanceOf` over public RPC at the same block for 20 randomly picked holders. All 20 matched to the last unit, and wallets the rebuild shows as fully withdrawn returned 0.
- **New wallets.** For 15 November we pulled every vault mint from public RPC with `eth_getLogs` in 100-block chunks (blocks 122,308,133 to 122,592,638). It returned the same 1,893 mints to the same recipients as HyperSync, and 788 of those wallets had never deposited before, the same as the indexer.
- **Aave.** Aave's own API (`api.v3.aave.com`) reported a 56.10M mUSD reserve on Monad and a 56.01M supply position for the vault, in line with the RPC reads.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Build an Envio HyperIndex indexer (https://docs.envio.dev/docs/HyperIndex/overview) on Monad (chain 143)
for MetaMask's Money Account vault 0x1C8a336051D2024E318A229d01F9F6CF96efD316 from block 78633433.
Index its ERC-20 Transfer event. Keep every wallet's share balance, treat a mint (from the zero address)
as a deposit, and count wallets making their first deposit per UTC day.
```

## Learn more

- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview)
- [MetaMask Money Account](https://support.metamask.io/trade/money-account/)
