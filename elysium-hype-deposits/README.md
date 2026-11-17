# HYPE deposits into Elysium

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer for every message HyperEVM sends to Elysium, Kinetiq's Hyperliquid L2. Elysium settles to HyperEVM, so every deposit into Elysium goes through its Bridge contract on HyperEVM. The indexer reads that contract with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview) and counts native HYPE deposits, the wallets behind them and deposits per UTC day.

From the Bridge's first event on 19 Oct 2026 to HyperEVM block 51,087,189 (12 Nov 2026, about 18:03 UTC), **28,382 wallets made 46,963 native HYPE deposits into Elysium**. The busiest day was 9 Nov 2026, Elysium's public mainnet day, with 16,126 deposits and 10,883 first-time depositors.

| Day (UTC) | Deposits | New wallets |
| --- | ---: | ---: |
| 7 Nov 2026 | 3,808 | 2,271 |
| 8 Nov 2026 | 6,066 | 3,447 |
| 9 Nov 2026 | 16,126 | 10,883 |
| 10 Nov 2026 | 3,618 | 2,340 |

Over the same window the Bridge delivered 2.6M messages in all, and deposits sent straight to the Inbox carried 381,459.67 HYPE.

## Why it's interesting

A new chain's launch shows up first on the bridge. Every wallet that moved HYPE across is one `MessageDelivered` event on HyperEVM, so you can watch Elysium's first users arrive day by day without running an Elysium node.

HyperEVM is on HyperSync, so a full backfill of the 2.6M bridge messages takes about a minute.

## What it indexes and stores

It listens to `MessageDelivered` on the Bridge from HyperEVM block 48,956,737, the Bridge's first event, and also selects the transaction's `hash`, `from`, `to` and `value`.

| Contract | Chain | Address |
| --- | --- | --- |
| Bridge | HyperEVM (999) | [`0x503D572157113fAaaD4DbeD2647Bb10b949216B6`](https://hyperevmscan.io/address/0x503D572157113fAaaD4DbeD2647Bb10b949216B6) |
| Inbox | HyperEVM (999) | [`0xce59f8B65ad41C9DAE4c07A0571a39824bD92cff`](https://hyperevmscan.io/address/0xce59f8B65ad41C9DAE4c07A0571a39824bD92cff) |

Both come from Elysium's [contract addresses page](https://elysium.kinetiq.xyz/docs/contract-addresses). The indexer only subscribes to the Bridge. The Inbox address is used to tell direct deposits apart.

The handler is [`src/handlers/Bridge.ts`](src/handlers/Bridge.ts). Each message has a `kind`, using Arbitrum Nitro message kinds. 12 is a native deposit (HYPE on Elysium, since HYPE is its gas token), 9 is a retryable ticket (token bridging through the gateways) and 3 is an L2 message.

- **`Totals`** is one row with id `elysium`, holding every message, kind 12 deposits, distinct depositors, `hypeDepositedDirect` and the last block seen.
- **`MessageKind`** counts messages per kind.
- **`Depositor`** has one row per wallet, with its number of deposits and the UTC day of its first one. The depositor is the event's `sender`, the wallet that called the Inbox.
- **`DailyDeposits`** has deposits and first-time depositors per UTC day.

`hypeDepositedDirect` sums the transaction value (in wei) of kind 12 deposits whose transaction went straight to the Inbox. Deposits routed through another contract still count in `hypeDeposits`, but not in this sum.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
git clone https://github.com/enviodev/hypersync-use-cases.git
cd hypersync-use-cases/elysium-hype-deposits
export ENVIO_API_TOKEN=your-token
pnpm install
pnpm codegen
pnpm dev
```

The GraphQL playground is at http://localhost:8080 (local admin secret `testing`).

```graphql
{
  Totals { messages hypeDeposits depositors hypeDepositedDirect lastBlock }
  MessageKind { id messages }
  DailyDeposits(order_by: { id: asc }) { id deposits newDepositors }
}
```

At block 51,087,189 the message kinds were 3 (2,516,826), 9 (49,804), 12 (46,963), 13 (838), 7 (15) and 11 (1). Your numbers will be higher, since the indexer keeps following the chain.

### Make it live

There's no `end_block` in `config.yaml`, so `pnpm dev` backfills and then keeps following HyperEVM's head. Add `end_block` under the chain to stop at a fixed block.

### Deploy it

Push your fork to GitHub and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service) to get a hosted GraphQL endpoint.

## Check the numbers

- **HyperSync.** A separate HyperSync script pulled every `MessageDelivered` log on the Bridge to block 51,086,631 and decoded the kind itself. It found 46,956 kind 12 deposits from 28,378 wallets at that block, in line with the indexer's 46,963 and 28,382 a few hundred blocks later, and the same count for each UTC day.
- **HyperRPC.** The same logs pulled through [HyperRPC](https://docs.envio.dev/docs/HyperRPC/overview-hyperrpc) with plain `eth_getLogs` gave an identical result to block 51,084,573 (2,614,101 messages, 46,941 deposits, 28,372 wallets).
- **Public RPC, as the comparison.** For 9 Nov 2026 we pulled the Bridge's `MessageDelivered` logs from a public HyperEVM RPC (blocks 50,757,651 to 50,845,490 in 200-block chunks). It returned 152,243 messages and 16,126 native deposits, the same 16,126 the indexer has for that day.
- **Bridge balance, as the comparison.** `eth_getBalance` on the Bridge returned 460,001 HYPE on four public HyperEVM RPCs at block 51,087,239. That's the HYPE locked behind Elysium's native gas token, and it isn't something the indexer measures.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
This is an Envio HyperIndex indexer for Elysium's Bridge on HyperEVM (chain 999).
Read README.md, config.yaml, schema.graphql and src/handlers/Bridge.ts, then the
HyperIndex docs at https://docs.envio.dev/docs/HyperIndex/overview. My API token
is in the ENVIO_API_TOKEN environment variable.

Add an hourly rollup of kind 12 deposits next to DailyDeposits, keyed by UTC
hour. Set end_block to 51087189 in config.yaml, run `pnpm codegen` and
`pnpm dev`, and check that the hourly deposits for 2026-11-09 add up to the
16,126 in DailyDeposits for that day.
```

## Links

- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview)
- [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [Token bridging on Elysium](https://elysium.kinetiq.xyz/docs/token-bridging-on-elysium)
- [Uniswap v4 pools on Elysium](../elysium-uniswap-v4-pools), the same idea on the Elysium side, synced over RPC
- [Envio Discord](https://discord.gg/envio)
