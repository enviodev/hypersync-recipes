# Solana Subscriptions

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana) indexer for Solana's Subscriptions and Allowances program. It records every plan, every subscription and every pull a merchant or delegatee makes, decoded straight from the program's own Codama IDL.

These are the numbers behind Envio's post on Solana Subscriptions. On 30 October, Solana Foundation's [@dev_jodee wrote up](https://x.com/dev_jodee/status/2116257337694425154) how Helius bills customers through the program: 700+ pulls, about 400 wallets and 150k+ USDC since launch. [@solana_devs shared it](https://x.com/solana_devs/status/2116525707690148178) the next day. This indexer counts the same thing from the chain, for Helius and for every other merchant.

## What we found

From the program's first transaction (1 May 2026) to slot 468089736 (11 November 2026, 10:27 UTC):

- **Helius has pulled 202,080 USDC** in 791 pulls from 434 wallets. Up to the moment of the 30 October post the indexer counts 703 pulls, 394 wallets and 176,581 USDC, which lines up with "700+ pulls, ~400 wallets, 150k+ USDC".
- **Subscription plans have pulled 220,721 USDC** in 1,305 USDC pulls. Helius accounts for 92% of that.
- **1,027 subscriptions** have been created, by 842 wallets, to plans from 54 merchants.
- **About 80 subscription pulls a week** for the last four full weeks (79, 83, 71 and 80, weeks starting 12 October to 2 November).
- **Allowances are the busier side.** 9,827 fixed and recurring allowances have been granted, and recurring allowances have been spent 122,673 times for 586,650 USDC. Most of those are small and made by another program through CPI: the median recurring pull is 0.01 USDC.

| | Pulls | USDC pulled |
|---|---:|---:|
| Subscription plans, Helius | 791 | 202,080 |
| Subscription plans, everyone else | 514 | 18,641 |
| Recurring allowances | 122,673 | 586,650 |
| Fixed allowances | 36 | 4 |

Rows count USDC pulls only. 435 more pulls moved other tokens and are in the `Pull` entity.

## The program

| | |
|---|---|
| Program ID | `De1egAFMkMWZSN5rYXRj9CAdheBamobVNubTsi9avR44` |
| Source | [solana-program/subscriptions](https://github.com/solana-program/subscriptions) |
| IDL | Codama, `idl/subscriptions.json` in that repo, copied unchanged to `idls/subscriptions.json` |
| Docs | [solana.com/docs/payments/subscriptions](https://solana.com/docs/payments/subscriptions/overview) |

For each wallet and mint the program sets one Subscription Authority as the token account's delegate. A merchant publishes a `Plan`, a wallet calls `subscribe`, and from then on the merchant, or a puller it allows, calls `transferSubscription` once each billing period. Fixed and recurring allowances (`createFixedDelegation`, `createRecurringDelegation`) work the same way, spent with `transferFixed` and `transferRecurring`.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and an API token from the [Envio Dashboard](https://envio.dev/app/api-tokens).

```bash
cp .env.example .env   # then paste your token into it
pnpm install
pnpm codegen
pnpm dev
```

The whole history is about 125k matched instructions and takes around 12 minutes on a laptop. When it finishes, open the GraphQL playground at http://localhost:8080:

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

`pnpm full-run` runs the same handlers in memory, without Docker, and writes `out/summary.json`, `out/pulls.json` and `out/subscriptions.json`. Set `END_SLOT` to stop somewhere else.

`pnpm test` decodes one real Helius pull (slot 452364379) and checks the amount, mint and receiver.

## How it counts

- `config.yaml` points `idl:` at the program's Codama IDL, so every instruction name, discriminator, account and argument comes from the file.
- Codegen skips `createPlan` and `updatePlan`, because their 128-byte `metadataUri` uses a Codama type HyperIndex does not decode yet. `createPlan` is declared again by hand in `config.yaml` with the same layout, which brings it back. `updatePlan` is not indexed.
- A pull is one `transferSubscription`, `transferRecurring` or `transferFixed` instruction, top-level or inner. The amount and mint come from the instruction's own `transferData`.
- A subscription is one `subscribe` instruction. Cancelling and resuming are not subtracted.
- Helius is the merchant `GjHgEpmTBUWwqhooG3krbZW4rKoxj1xEoiftFMS7kMCq`. All of its pulls are paid into one USDC account, `G2wv6MCDcaiqhbP4JqP6RB76utwAhhG4BoZ71r58zgk6`.
- Only successful transactions count. HyperSync does not serve the instructions of failed transactions.
- Weeks start Monday 00:00 UTC.

## How we checked it

- **Against Solana RPC, program-wide.** `getSignaturesForAddress` on the program returns 148,123 successful transactions. Every one of the 123,551 transactions the indexer recorded a pull or subscription in is among them.
- **Against Solana RPC, for Helius.** We listed every successful transaction that touches both the program and Helius's USDC account (792), fetched each one with `getTransaction`, and decoded the program's instructions ourselves with `verify/rpc_check.py`. Inside the indexed window all 791 pulls match the indexer one for one, for 202,080.25 USDC, and in every one the treasury's USDC balance rose by exactly the instruction's amount. The 792nd transaction is a 49 USDC pull in slot 468090995, just after the window. `verify/compare.py` does the comparison.
- **Against Helius's own numbers.** Cut at the 30 October post, the indexer's Helius totals (703 pulls, 394 wallets, 176,581 USDC) match the post's 700+, about 400 and 150k+.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Build an Envio HyperIndex indexer on Solana (https://docs.envio.dev/docs/HyperIndex/solana)
for the Solana Subscriptions program, De1egAFMkMWZSN5rYXRj9CAdheBamobVNubTsi9avR44.
Point idl: at the Codama IDL from github.com/solana-program/subscriptions (idl/subscriptions.json).
Record every subscribe call, and every transferSubscription, transferRecurring and
transferFixed pull with its amount and mint from transferData. Keep running totals and
a weekly roll-up of USDC pulled. My API token is in the ENVIO_API_TOKEN environment variable.
```

## Learn more

- [Indexing on Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Decoding instructions with an IDL](https://docs.envio.dev/docs/HyperIndex/solana/decoding)
- [Solana instruction handlers](https://docs.envio.dev/docs/HyperIndex/solana/instruction-handlers)
- [Helius: setting up subscriptions and recurring payments on Solana](https://www.helius.dev/blog/solana-subscriptions-recurring-payments)
