# HYPE deposits into Elysium

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/overview) indexer for every message HyperEVM sends to Elysium, Kinetiq's Hyperliquid L2. Elysium settles to HyperEVM, so every deposit into Elysium goes through its Bridge contract on HyperEVM. The indexer reads that contract with [HyperSync](https://docs.envio.dev/docs/HyperSync/overview) and counts native HYPE deposits, the wallets behind them and deposits per UTC day.

HyperEVM is on HyperSync, so a full backfill of 2.6M bridge messages takes about a minute.

## Contracts

| Contract | Chain | Address |
|---|---|---|
| Bridge | HyperEVM | `0x503D572157113fAaaD4DbeD2647Bb10b949216B6` |
| Inbox | HyperEVM | `0xce59f8B65ad41C9DAE4c07A0571a39824bD92cff` |

Both come from Elysium's [contract addresses page](https://elysium.kinetiq.xyz/docs/contract-addresses). The indexer starts at HyperEVM block 48,956,737, the Bridge's first event (19th October 2026).

## The indexer

`config.yaml`:

```yaml
field_selection:
  transaction_fields: [hash, from, to, value]
contracts:
  - name: Bridge
    events:
      - event: MessageDelivered(uint256 indexed messageIndex, bytes32 indexed beforeInboxAcc, address inbox, uint8 kind, address sender, bytes32 messageDataHash, uint256 baseFeeL1, uint64 timestamp)
chains:
  - id: 999
    start_block: 48956737
    contracts:
      - name: Bridge
        address: 0x503D572157113fAaaD4DbeD2647Bb10b949216B6
```

The handler is [`src/handlers/Bridge.ts`](src/handlers/Bridge.ts).

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and an API token from the [Envio Dashboard](https://envio.dev/app/api-tokens).

```bash
export ENVIO_API_TOKEN=your-token
pnpm install
pnpm codegen
pnpm dev
```

The GraphQL playground is at http://localhost:8080 (admin secret `testing`).

## Deploy it on Envio Cloud

Push the folder to a GitHub repo and add it as an indexer in the [Envio Cloud dashboard](https://envio.dev/app). Envio Cloud backfills, follows HyperEVM's head and gives you a hosted GraphQL endpoint. See [Hosted service deployment](https://docs.envio.dev/docs/HyperIndex/hosted-service-deployment).

## Query it

```graphql
{
  Totals { messages hypeDeposits depositors hypeDepositedDirect lastBlock }
  MessageKind { id messages }
  DailyDeposits(order_by: { id: asc }) { id deposits newDepositors }
}
```

On 12th November 2026 at about 18:03 UTC (HyperEVM block 51,087,189) it returned:

```
Totals: messages 2,614,447 · hypeDeposits 46,963 · depositors 28,382 · hypeDepositedDirect 381,459.67 HYPE
MessageKind: 3 → 2,516,826 · 9 → 49,804 · 12 → 46,963 · 13 → 838 · 7 → 15 · 11 → 1
DailyDeposits (busiest days):
  2026-11-07   3,808 deposits    2,271 new wallets
  2026-11-08   6,066 deposits    3,447 new wallets
  2026-11-09  16,126 deposits   10,883 new wallets   (public mainnet day)
  2026-11-10   3,618 deposits    2,340 new wallets
```

Your numbers will be higher, since the indexer keeps following the chain.

## How it counts

- Every message from HyperEVM to Elysium is a `MessageDelivered` event on the Bridge, with a `kind`. These are Arbitrum Nitro message kinds: 12 is a native deposit (HYPE on Elysium, since HYPE is its gas token), 9 is a retryable ticket (token bridging through the gateways), 3 is an L2 message.
- A HYPE deposit is a kind 12 message. Its depositor is the `sender` on the event, the wallet that called the Inbox on HyperEVM.
- `newDepositors` counts each wallet once, on the UTC day of its first deposit.
- `hypeDepositedDirect` sums the transaction value of kind 12 deposits whose transaction went straight to the Inbox. Deposits routed through another contract still count in `hypeDeposits`, but not in this sum.

## How we checked it

- A separate HyperSync script pulled every `MessageDelivered` log on the Bridge to block 51,086,631 and decoded the kind itself. It found 46,956 kind 12 deposits from 28,378 wallets at that block, in line with the indexer's 46,963 and 28,382 a few hundred blocks later, and the same count per UTC day. The same logs pulled through [HyperRPC](https://docs.envio.dev/docs/HyperRPC/overview-hyperrpc) with plain `eth_getLogs` gave an identical result to block 51,084,573 (2,614,101 messages, 46,941 deposits, 28,372 wallets).
- For 9th November we pulled the Bridge's `MessageDelivered` logs from HyperEVM's public RPC (`rpc.hypurrscan.io`, blocks 50,757,651 to 50,845,490 in 200-block chunks). It returned 152,243 messages and 16,126 native deposits, the same 16,126 the indexer has for that day.
- `eth_getBalance` on the Bridge returned 460,001 HYPE on four public HyperEVM RPCs (rpc.hyperliquid.xyz, hyperliquid.drpc.org, rpc.hypurrscan.io, stakely) at block 51,087,239. That is the HYPE locked behind Elysium's native gas token.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Build an Envio HyperIndex indexer (https://docs.envio.dev/docs/HyperIndex/overview) on HyperEVM (chain 999)
for Elysium's Bridge 0x503D572157113fAaaD4DbeD2647Bb10b949216B6 from block 48956737. Index the Arbitrum
Nitro MessageDelivered event. Count every message by kind, and treat kind 12 as a native HYPE deposit:
count deposits, distinct depositor wallets (the event's sender) and deposits per UTC day.
```

## Learn more

- [HyperIndex overview](https://docs.envio.dev/docs/HyperIndex/overview)
- [Token bridging on Elysium](https://elysium.kinetiq.xyz/docs/token-bridging-on-elysium)
- [Uniswap v4 pools on Elysium](../elysium-uniswap-v4-pools), the same idea on the Elysium side, synced over RPC
