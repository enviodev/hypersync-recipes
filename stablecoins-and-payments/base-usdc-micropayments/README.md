# Gasless USDC payments on Base, by size

Reads every gasless USDC payment on Base in a time window, using [Envio HyperSync](https://docs.envio.dev/docs/HyperSync/overview), and sizes each one. It prints how many there were, how many were worth a cent or less, what those small payments added up to, and when they happened.

These are the numbers behind Envio's post on tiny USDC payments on Base.

## Run it

You need Python 3 and a HyperSync API token from the [Envio Dashboard](https://envio.dev/app/api-tokens). The script has no other dependencies.

```bash
export ENVIO_API_TOKEN=your-token
python script.py                        # the last 24 hours
python script.py 24 2026-11-09T17:07    # 24 hours ending at a UTC time
```

## What it prints

```
Base USDC, 2026-11-08 17:07 UTC to 2026-11-09 17:07 UTC (blocks 54,836,222 to 55,268,222)
Gasless USDC payments (AuthorizationUsed): 204,152 from 7,023 wallets
Worth a cent or less: 79,348 from 4,486 wallets, $324.42 in total
  at $0.001 or less        34,020
  between $0.001 and $0.01 25,197
  at $0.01                 20,131
Payments of a cent or less, by hour (UTC)
  00:00  3,557
  01:00  3,652
  ...
  23:00  5,722
```

Run it without a time and you get the latest 24 hours, so your numbers will differ.

## How it counts

- USDC on Base is `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`, from Circle's [USDC contract addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses).
- A gasless USDC payment is a signed [EIP-3009](https://eips.ethereum.org/EIPS/eip-3009) `transferWithAuthorization` or `receiveWithAuthorization`. The payer signs, someone else submits the transaction and pays the gas, and USDC emits `AuthorizationUsed` with the payer's address.
- This is the transfer method the x402 [exact scheme on EVM](https://github.com/x402-foundation/x402/blob/main/specs/schemes/exact/scheme_exact_evm.md) uses by default for USDC. Other apps use it too, so these counts cover all gasless USDC payments on Base, not only x402.
- The script asks HyperSync for the `AuthorizationUsed` logs with `join_mode: JoinAll`, which returns every log in the same transactions. The USDC `Transfer` from the payer in that transaction gives the payment size.
- "A cent or less" means 0.01 USDC or less. Wallets are distinct payers.
- The time window is found by block timestamp, since Base produces a block every 0.2 seconds.

## Ask your coding agent

Paste this into Claude Code, Cursor or any coding agent:

```
Use Envio HyperSync (https://docs.envio.dev/docs/HyperSync/overview) to read every AuthorizationUsed
event on Base USDC (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913) for the last 7 days, with join_mode
JoinAll so each payment's USDC Transfer comes back too. My API token is in the ENVIO_API_TOKEN
environment variable. Chart payments of a cent or less per day, and the wallets making them.
```

## Learn more

- [Index Base with Envio](https://envio.dev/chains/base)
- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Why AI agents acting onchain need an indexer](https://docs.envio.dev/blog/ai-agents-acting-onchain-indexer)
- [How to index USDC transfers on Arc](https://docs.envio.dev/blog/index-arc-usdc-transfers)
- [HyperIndex, for a full indexer with a GraphQL API](https://docs.envio.dev/docs/HyperIndex/overview)
