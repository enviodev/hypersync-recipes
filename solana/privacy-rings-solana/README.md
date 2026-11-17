# Shielded pool activity on Solana

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana) indexer for a pair of Solana programs that run a shielded pool. Users register once in a user registry, then deposit tokens into the pool, send private transfers inside it and withdraw back out. The indexer reads both programs at the instruction level from their first mainnet activity, then follows the chain head live.

From the first activity on either program (slot 462,230,000, 27 Oct 2026) to slot 468,092,121 (11 Nov 2026), **the shielded pool received 2,180 top-level `transact` calls**, the proven transactions that carry private transfers and public deposits and withdrawals. The programs went live publicly on 10 Nov 2026, so earlier activity is pre-launch.

It counts activity. It never decodes amounts, and it stores no owner, viewing or nullifier keys.

## Why it's interesting

Shielded pools are hard to read, because the useful parts are hidden on purpose. What you can see is each instruction and whether a proven transaction carries a public deposit or withdrawal leg. That's enough to count registrations, deposits, withdrawals and fully private transfers, without touching anything the user meant to keep private.

These programs also ship without an Anchor or Codama IDL, so it's a good example of declaring Solana instructions by hand in HyperIndex.

## What it indexes and stores

| Program | Program ID |
| --- | --- |
| Shielded pool | `ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW` |
| User registry | `regy3WAeRXMYuMYxr5iK3Bf9Arr3PcxGxyzAddbiqDQ` |

Every instruction starts with a 1-byte tag, defined in the programs' open-source interface crates, and `config.yaml` declares each one by hand.

- **Shielded pool tags.** `deposit` 15, `transact` 16, `merge_transact` 17, `ring_deposit` 18, `ring_transact` 19, `ring_merge_transact` 20, `ring_authority_transact` 21.
- **User registry tags.** `register` 0. Its arguments (a 32-byte nullifier key and a 33-byte viewing key) are plain Borsh, so `config.yaml` declares them and HyperIndex decodes them, but the handler reads only the user record account.

The proven transactions (`transact`, `ring_transact` and `ring_authority_transact`) carry any public deposit or withdrawal as `interface_transfers` near the start of the instruction data. [`src/lib/interfaceLegs.ts`](src/lib/interfaceLegs.ts) reads only the direction of each leg (SOL or SPL, in or out), never the amount. A call with one or more withdrawal legs is a `Withdrawal`, one with deposit legs only is a `Deposit`, and one with no legs is a `PrivateTransfer`. `deposit` and `ring_deposit` are deposits, and the two merge instructions are `Merge`.

The `EMIT_EVENT` tag (14) is left out on purpose. Anyone can call it with forged bytes, so the indexer reads the state-changing instructions directly instead.

The handler is [`src/handlers/PrivacyRings.ts`](src/handlers/PrivacyRings.ts). It stores three entities.

- **`PoolAction`** has one row per shielded-pool instruction, with its kind, instruction name, number of deposit and withdrawal legs, whether it was an inner (CPI) call, slot, block time and transaction signature.
- **`Registration`** has one row per user registry `register` call.
- **`Totals`** is one row with id `mainnet`, holding registrations, deposits, withdrawals, private transfers, merges and the last slot seen.

Only successful transactions count. Inner (CPI) calls are counted too, and `isInner` marks them.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). The test reads real slots from HyperSync, so it needs the token too.

```bash
git clone https://github.com/enviodev/hypersync-use-cases.git
cd hypersync-use-cases/solana/privacy-rings-solana
cp .env.example .env   # then paste your token into ENVIO_API_TOKEN
pnpm install
pnpm codegen
pnpm test              # replays real mainnet slots 463,205,308 to 463,208,400
pnpm dev
```

The GraphQL playground is at http://localhost:8080 (local admin secret `testing`).

```graphql
{
  Totals { registrations deposits withdrawals privateTransfers merges lastSlot }
  PoolAction(order_by: { slot: desc }, limit: 10) { kind instruction slot txSignature }
}
```

### Make it live

There's no `end_slot` in `config.yaml`, so `pnpm dev` backfills from slot 462,230,000 and then indexes new slots as they land. Set `start_slot: latest` to skip the history. Set `ENVIO_TUI=false` to see each new instruction in the log once it's caught up.

```
INFO: Deposit · slot 468094125
```

Filter `PoolAction` by `slot` or `timestamp` if you only want activity after the 10 Nov 2026 launch.

### Deploy it

Push your fork to GitHub and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service) to get a hosted GraphQL endpoint.

## Check the numbers

- **HyperSync.** A separate script pulled every instruction call to both programs straight from [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana), from slot 462,230,000 to 468,092,121, and counted them by tag. The indexer's totals at the head matched that count exactly for every kind.
- **The leg parser.** It read all 2,180 top-level `transact` calls in that range without hitting an unknown variant.
- **The test.** `pnpm test` replays a real slot window with two registrations, one deposit, one private transfer and one withdrawal, and checks each total.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
This is an Envio HyperIndex indexer for Solana (ecosystem: svm) covering a
shielded pool (ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW) and its user registry
(regy3WAeRXMYuMYxr5iK3Bf9Arr3PcxGxyzAddbiqDQ). Read README.md, config.yaml,
schema.graphql, src/handlers/PrivacyRings.ts, src/lib/interfaceLegs.ts and
src/indexer.test.ts, then https://docs.envio.dev/docs/HyperIndex/solana. My API
token is in the ENVIO_API_TOKEN environment variable.

Add a DailyStat entity with registrations, deposits, withdrawals and private
transfers per UTC day. Do not store amounts or keys. Extend the existing test
to check the daily row for slots 463205308 to 463208400, then run
`pnpm codegen` and `pnpm test` until they pass.
```

## Links

- [Indexing Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Decoding instructions without an IDL](https://docs.envio.dev/docs/HyperIndex/solana/decoding#programs-without-an-idl)
- [Solana instruction handlers](https://docs.envio.dev/docs/HyperIndex/solana/instruction-handlers)
- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Envio Discord](https://discord.gg/envio)
