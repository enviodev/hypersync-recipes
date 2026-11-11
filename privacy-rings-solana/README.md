# Helius Privacy Rings on Solana

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana) indexer for Solana Privacy Rings, which Helius launched on Solana mainnet on 10th November 2026. It indexes the two Privacy Rings programs at the instruction level: user registrations, deposits into the shielded pool, withdrawals out of it, private transfers inside it, and note merges. It syncs from the first mainnet activity and then follows the chain head live.

It counts activity. It never decodes amounts, and it stores no owner, viewing or nullifier keys.

## Programs

| Program | Program ID |
|---|---|
| Shielded pool | `ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW` |
| User registry | `regy3WAeRXMYuMYxr5iK3Bf9Arr3PcxGxyzAddbiqDQ` |

Both IDs come from Helius's [release notes](https://github.com/helius-labs/privacy-rings/releases) (`shielded-pool-v1.0.0` and `user-registry-v1.0.0`).

## How it decodes the instructions

Privacy Rings ships Pinocchio programs without an Anchor or Codama IDL, so `config.yaml` declares each instruction by hand. Every instruction starts with a 1-byte tag, defined in Helius's interface crates:

- Shielded pool tags, from [`program-libs/event/src/tag.rs`](https://github.com/helius-labs/privacy-rings/blob/main/program-libs/event/src/tag.rs): `deposit` 15, `transact` 16, `merge_transact` 17, `ring_deposit` 18, `ring_transact` 19, `ring_merge_transact` 20, `ring_authority_transact` 21.
- User registry tags, from [`program-libs/user-registry-interface/src/instruction.rs`](https://github.com/helius-labs/privacy-rings/blob/main/program-libs/user-registry-interface/src/instruction.rs): `register` 0. Its arguments (a 32-byte nullifier key and a 33-byte viewing key) are plain Borsh, so `config.yaml` declares them and HyperIndex decodes them. The handler reads only the user record account.

The shielded pool's proven transactions (`transact` and the ring variants) carry any public deposit or withdrawal as `interface_transfers` near the start of the instruction data. The handler reads only the direction of each leg (SOL or SPL, in or out), in [`src/lib/interfaceLegs.ts`](src/lib/interfaceLegs.ts):

- one or more withdrawal legs: `Withdrawal`
- deposit legs only: `Deposit`
- no legs: `PrivateTransfer`

The `EMIT_EVENT` tag (14) is left out on purpose. Helius's source notes that anyone can call it with forged bytes, so indexers have to tie events to a parent instruction. This indexer reads the state-changing instructions directly instead.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and an API token from the [Envio Dashboard](https://envio.dev/app/api-tokens).

```bash
cp .env.example .env   # then paste your token into it
pnpm install
pnpm codegen
pnpm test              # replays real mainnet slots 463,205,308 to 463,208,400
pnpm dev
```

`pnpm dev` backfills from slot 462,230,000 (27th October 2026, the first activity on either program) and then indexes new slots as they land. Set `ENVIO_TUI=false` to see each new instruction in the log:

```
INFO: Deposit · slot 468094125
```

The GraphQL playground is at http://localhost:8080 (admin secret `testing`).

```graphql
{
  Totals { registrations deposits withdrawals privateTransfers merges lastSlot }
  PoolAction(order_by: { slot: desc }, limit: 10) { kind instruction slot txSignature }
}
```

## What it stores

- `PoolAction`: one row per shielded-pool instruction, with its kind, instruction name, number of deposit and withdrawal legs, slot, block time and transaction signature.
- `Registration`: one row per user registry `register` call.
- `Totals`: running counts, one row with id `mainnet`.

Only successful transactions are counted. Inner (CPI) calls are counted too, and `isInner` marks them.

## How we checked it

- We pulled every instruction call to both programs straight from [HyperSync for Solana](https://docs.envio.dev/docs/HyperSync/solana) from slot 462,230,000 to 468,092,121 and counted them by tag in a separate script. The indexer's totals at the head matched that count exactly for every kind.
- The leg parser read all 2,180 top-level `transact` calls in that range without hitting an unknown variant.
- `pnpm test` replays a real slot window with two registrations, one deposit, one private transfer and one withdrawal, and checks each total.

Activity from 27th October to the 10th November launch looks like Helius testing on mainnet. Filter by `slot` or `timestamp` if you only want post-launch activity.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Build an Envio HyperIndex Solana indexer (https://docs.envio.dev/docs/HyperIndex/solana) for
Helius Privacy Rings. Shielded pool ring1GaLCuJnkUMVkX2JeZLTTX17wKsV4fZmPVzXANW, user registry
regy3WAeRXMYuMYxr5iK3Bf9Arr3PcxGxyzAddbiqDQ. There is no IDL: declare each instruction with its
1-byte discriminator from helius-labs/privacy-rings program-libs/event/src/tag.rs and
program-libs/user-registry-interface/src/instruction.rs. Count registrations, deposits,
withdrawals and private transfers. Do not store amounts or keys.
```

## Learn more

- [Indexing on Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Decoding instructions without an IDL](https://docs.envio.dev/docs/HyperIndex/solana/decoding#programs-without-an-idl)
- [Solana instruction handlers](https://docs.envio.dev/docs/HyperIndex/solana/instruction-handlers)
- [helius-labs/privacy-rings](https://github.com/helius-labs/privacy-rings)
