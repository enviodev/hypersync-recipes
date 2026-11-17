# Gasless USDC payments on Base, by size

In the 24 hours to 9 Nov 2026 17:07 UTC, **Base saw 204K gasless USDC payments from 7K wallets**. 79.3K of them were worth a cent or less, sent by 4.5K wallets, and together they added up to $324.42.

| Size | Payments |
| --- | --- |
| $0.001 or less | 34,020 |
| Between $0.001 and $0.01 | 25,197 |
| Exactly $0.01 | 20,131 |
| All gasless payments | 204,152 |

## Why it's interesting

Payments this small only make sense when someone else pays the gas. That's how x402 and other agent payment flows work, so counting sub-cent USDC payments is a direct way to see machine-to-machine payments happening onchain. The script also shows a handy HyperSync trick, pulling an event and every other log in the same transaction in one query.

## What it pulls

- Every `AuthorizationUsed` log on USDC on Base [`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`](https://basescan.org/address/0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913), from Circle's [USDC contract addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses).
- USDC emits `AuthorizationUsed` for every signed [EIP-3009](https://eips.ethereum.org/EIPS/eip-3009) `transferWithAuthorization` or `receiveWithAuthorization`. The payer signs, someone else submits the transaction and pays the gas.
- The query uses `join_mode: JoinAll`, which returns every log in the same transactions. The USDC `Transfer` from the payer in that transaction gives the payment size.

This is the method the x402 [exact scheme on EVM](https://github.com/x402-foundation/x402/blob/main/specs/schemes/exact/scheme_exact_evm.md) uses for USDC by default. Other apps use it too, so the counts cover every gasless USDC payment on Base, not x402 alone. "A cent or less" means 0.01 USDC or less, and wallets are distinct payers. Every number here comes from HyperSync.

## Run it

You need Python 3 and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens). There's nothing else to install.

```bash
export ENVIO_API_TOKEN=your-token
python3 script.py                        # the last 24 hours
python3 script.py 24 2026-11-09T17:07    # the window above
```

Sample output from the window above.

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

Without an end time you get the latest 24 hours, so your numbers will differ.

## Change the window or chain

- **Window.** The first argument is the number of hours and the second is an end time in UTC. The script finds the matching blocks by timestamp.
- **Size.** The cent cut-off is the `0.01` in the line that builds `small`. Change it to size payments another way.
- **Chain.** USDC supports EIP-3009 wherever Circle issues it. Change `URL` to another chain's endpoint from the [supported networks list](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks) and `USDC` to Circle's address there.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent.

```text
Read script.py and README.md in this folder. It uses HyperSync
(https://docs.envio.dev/docs/HyperSync/overview) to read every AuthorizationUsed
log on USDC on Base, with join_mode JoinAll so each payment's Transfer comes back
in the same query. My HyperSync token is in the ENVIO_API_TOKEN environment variable.

Group the payments of a cent or less by the address that received them, and print
the 20 receivers with the most payments over the last 7 days, one row per day.
Keep the standard library only. Then pick one transaction from the output and check
its AuthorizationUsed and Transfer logs against the receipt on https://base-rpc.publicnode.com.
```

## Links

- [HyperSync overview](https://docs.envio.dev/docs/HyperSync/overview)
- [HyperSync query reference](https://docs.envio.dev/docs/HyperSync/hypersync-query)
- [Raw HTTP query examples](https://docs.envio.dev/docs/HyperSync/hypersync-curl-examples), the same plain requests this script makes
- [HyperSync supported networks](https://docs.envio.dev/docs/HyperSync/hypersync-supported-networks)
- [EIP-3009](https://eips.ethereum.org/EIPS/eip-3009)
- [x402 exact scheme on EVM](https://github.com/x402-foundation/x402/blob/main/specs/schemes/exact/scheme_exact_evm.md)
- [Envio Discord](https://discord.gg/envio)
