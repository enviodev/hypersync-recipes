# Solana Subscriptions

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana) indexer for Solana's Subscriptions and Allowances program. It records every plan, every subscription and every pull a merchant or delegatee makes, decoded straight from the program's own Codama IDL.

From the program's first transaction (1 May 2026) to slot 468,089,736 (11 Nov 2026, 10:27 UTC), **1,027 subscriptions were created by 842 wallets, to plans from 54 merchants, and subscription plans pulled 220,721 USDC** in 1,305 USDC pulls. Allowances are the busier side. 9,827 fixed and recurring allowances were granted, and recurring allowances were spent 122,673 times for 586,650 USDC.

| | Pulls | USDC pulled |
| --- | ---: | ---: |
| Subscription plans, merchant `GjHgEpmTBUWwqhooG3krbZW4rKoxj1xEoiftFMS7kMCq` | 791 | 202,080 |
| Subscription plans, every other merchant | 514 | 18,641 |
| Recurring allowances | 122,673 | 586,650 |
| Fixed allowances | 36 | 4 |

Rows count USDC pulls only. 435 more pulls moved other tokens and are in the `Pull` entity.

One merchant, `GjHgEpmTBUWwqhooG3krbZW4rKoxj1xEoiftFMS7kMCq`, pulled 202,080 USDC in 791 pulls from 434 wallets, all paid into one USDC token account, `G2wv6MCDcaiqhbP4JqP6RB76utwAhhG4BoZ71r58zgk6`. Across all merchants there were about 80 USDC subscription pulls a week for the last four full weeks of the window (79, 83, 71 and 80, for the weeks starting 12 Oct to 2 Nov 2026).

## Why it's interesting

This is onchain recurring billing. A wallet approves a plan once, and the merchant pulls each period's payment itself, with no card network in the middle. The indexer shows who's actually billing through it and how often.

The allowance side looks different. Most recurring allowance spends are small and made by another program through CPI, and the median one is 0.01 USDC. HyperIndex counts inner instructions too, so those show up.

## What it indexes and stores

| | |
| --- | --- |
| Program ID | `De1egAFMkMWZSN5rYXRj9CAdheBamobVNubTsi9avR44` |
| Source | [solana-program/subscriptions](https://github.com/solana-program/subscriptions) |
| IDL | Codama, `idl/subscriptions.json` in that repo, copied unchanged to `idls/subscriptions.json` |
| Docs | [solana.com/docs/payments/subscriptions](https://solana.com/docs/payments/subscriptions/overview) |

For each wallet and mint, the program sets one Subscription Authority as the token account's delegate. A merchant publishes a `Plan`, a wallet calls `subscribe`, and from then on the merchant, or a puller it allows, calls `transferSubscription` once each billing period. Fixed and recurring allowances (`createFixedDelegation`, `createRecurringDelegation`) work the same way, spent with `transferFixed` and `transferRecurring`.

`config.yaml` points `idl:` at the Codama IDL, so every instruction name, discriminator, account and argument comes from that file. Codegen skips `createPlan` and `updatePlan`, because their 128-byte `metadataUri` uses a Codama type HyperIndex doesn't decode yet. `createPlan` is declared again by hand in `config.yaml` with the same layout, which brings it back. `updatePlan` isn't indexed, and `pnpm codegen` prints a warning saying so.

The handler is [`src/handlers/Subscriptions.ts`](src/handlers/Subscriptions.ts). It stores five entities.

- **`Plan`** has one row per plan, with merchant, mint, price, period and its subscriptions and pulls.
- **`Subscription`** has one row per `subscribe` call. Cancelling and resuming aren't subtracted.
- **`Pull`** has one row per `transferSubscription`, `transferRecurring` or `transferFixed` instruction, top-level or inner. The amount and mint come from the instruction's own `transferData`.
- **`WeeklyStat`** has USDC pulls, USDC pulled and new subscriptions per week, starting Monday 00:00 UTC. Its `pulls` count every USDC pull, allowances included.
- **`Totals`** is one row with id `mainnet`.

Only successful transactions count, since HyperSync doesn't serve the instructions of failed transactions.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
git clone https://github.com/enviodev/hypersync-use-cases.git
cd hypersync-use-cases/solana/solana-subscriptions
cp .env.example .env   # then paste your token into ENVIO_API_TOKEN
pnpm install
pnpm codegen
pnpm test
pnpm dev
```

`pnpm test` decodes one real subscription pull in slot 452,364,379 and checks its amount, mint and receiver. The whole history is about 125K matched instructions and takes around 12 minutes on a laptop. When it finishes, open the GraphQL playground at http://localhost:8080 (local admin secret `testing`).

```graphql
{
  Totals(where: { id: { _eq: "mainnet" } }) {
    subscriptions
    pulls
    usdcPulls
    usdcPulled
  }
  WeeklyStat(order_by: { weekStart: asc }) {
    weekStart
    pulls
    usdcPulled
    subscriptions
  }
}
```

`pnpm full-run` runs the same handlers in memory, without Docker, and writes `out/summary.json`, `out/pulls.json` and `out/subscriptions.json`. It stops at slot 468,090,000 unless you set `END_SLOT`.

### Make it live

There's no `end_slot` in `config.yaml`, so `pnpm dev` backfills from slot 416,950,000 and then keeps following Solana's head. To skip the history, set `start_slot: latest`.

### Deploy it

Push your fork to GitHub and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service) to get a hosted GraphQL endpoint.

## Check the numbers

`verify/` has the scripts we used. Solana RPC is the outside source here, used as the comparison.

- **Program-wide.** `getSignaturesForAddress` on the program returns 148,123 successful transactions. Every one of the 123,551 transactions the indexer recorded a pull or subscription in is among them.
- **One merchant's pulls.** We listed every successful transaction that touches both the program and the USDC account `G2wv6MCDcaiqhbP4JqP6RB76utwAhhG4BoZ71r58zgk6` (792), fetched each one with `getTransaction` and decoded the program's instructions ourselves with `verify/rpc_check.py`. Inside the window all 791 pulls match the indexer one for one, for 202,080.25 USDC, and in every one the account's USDC balance rose by exactly the instruction's amount. The 792nd transaction is a 49 USDC pull in slot 468,090,995, just after the window. `verify/compare.py` does the comparison.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
This is an Envio HyperIndex indexer for Solana's Subscriptions program
(De1egAFMkMWZSN5rYXRj9CAdheBamobVNubTsi9avR44, ecosystem: svm). Read README.md,
config.yaml, schema.graphql, src/handlers/Subscriptions.ts and
src/indexer.test.ts, then https://docs.envio.dev/docs/HyperIndex/solana. My API
token is in the ENVIO_API_TOKEN environment variable.

Add a Merchant entity with plans, subscribers, pulls and USDC pulled per
merchant, updated from createPlan, subscribe and transferSubscription. Add a
test for it next to the existing one, run `pnpm codegen` and `pnpm test` until
they pass, then run `pnpm full-run` and check that each merchant's USDC pulled matches the sum of its plans' pulled
amounts in out/summary.json.
```

## Links

- [Indexing Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Decoding instructions with an IDL](https://docs.envio.dev/docs/HyperIndex/solana/decoding)
- [Solana instruction handlers](https://docs.envio.dev/docs/HyperIndex/solana/instruction-handlers)
- [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Solana Subscriptions program](https://github.com/solana-program/subscriptions)
- [Envio Discord](https://discord.gg/envio)
