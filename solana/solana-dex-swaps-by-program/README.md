# Solana DEX swaps by program

A [HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana) indexer that counts every successful swap on Solana's main DEX programs, day by day, and splits each count into swaps sent straight to the DEX and swaps another program called in for you. Jupiter routes are counted on their own row.

Over the seven UTC days from 3 to 9 Nov 2026, **we counted 220.2M successful swaps across ten DEX programs, about 31M a day**. PumpSwap carried just over half. Meteora DAMM v2 came second with about 1 in 6, and more than 9 in 10 of its swaps were sent to it directly. Orca Whirlpool, Raydium CLMM and Meteora DLMM work the other way, with more than 8 in 10 of their swaps called in by another program such as the Jupiter aggregator.

| Program | Swaps | Share | Called by another program |
| --- | ---: | ---: | ---: |
| PumpSwap | 119.6M | 54.3% | 13% |
| Meteora DAMM v2 | 35.7M | 16.2% | 7% |
| Pump.fun curve | 28.3M | 12.8% | 76% |
| Orca Whirlpool | 11.0M | 5.0% | 88% |
| Raydium CLMM | 9.7M | 4.4% | 81% |
| Meteora DLMM | 9.0M | 4.1% | 91% |
| Raydium CPMM | 3.4M | 1.5% | 87% |
| Raydium LaunchLab | 1.7M | 0.8% | 82% |
| Raydium AMM v4 | 1.5M | 0.7% | 81% |
| Meteora DAMM v1 | 0.4M | 0.2% | 97% |
| Total | 220.2M | 100% | |
| Jupiter routes (not in the total) | 18.2M | | 21% |

Meteora DAMM v2's daily share stayed between 13% and 18% all week.

## Why it's interesting

On Solana a lot of trading never touches a DEX directly. An aggregator, a bot or another program calls the pool for you, and that swap only shows up as an inner (CPI) instruction. Count only top-level instructions and you'd miss most of the swaps on venues like Orca, Raydium CLMM and Meteora DLMM. HyperIndex sees both, and `isInner` tells them apart, so you get the real picture of who carries Solana's trading and how it reaches them.

## What it indexes and stores

Only instructions that trade are listed in `config.yaml`, so liquidity, fee, position and event-logging calls never match. Program IDs and instruction discriminators come from each project's own GitHub repo or published IDL.

| Program | Program ID | Swap instructions |
|---|---|---|
| Raydium AMM v4 | `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8` | SwapBaseIn, SwapBaseOut, SwapBaseInV2, SwapBaseOutV2 |
| Raydium CLMM | `CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK` | swap, swap_v2, swap_router_base_in |
| Raydium CPMM | `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C` | swap_base_input, swap_base_output |
| Raydium LaunchLab | `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj` | buy_exact_in, buy_exact_out, sell_exact_in, sell_exact_out |
| Orca Whirlpool | `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` | swap, swap_v2, two_hop_swap, two_hop_swap_v2 |
| Meteora DLMM | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` | swap, swap2, swap_exact_out, swap_exact_out2, swap_with_price_impact, swap_with_price_impact2 |
| Meteora DAMM v1 | `Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB` | swap |
| Meteora DAMM v2 | `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG` | swap, swap2 |
| PumpSwap | `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | buy, sell, buy_exact_quote_in, buy_v2, sell_v2, buy_exact_quote_in_v2, multi_hop_swap |
| Pump.fun bonding curve | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | buy, sell, buy_exact_sol_in, the v2 and v3 buys and sells, multi_hop_curve_swap |
| Jupiter v6 (routes only) | `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4` | route, shared_accounts_route, exact_out_route and their v2, token-ledger and attestation variants |

Sources are [raydium-amm](https://github.com/raydium-io/raydium-amm), [raydium-idl](https://github.com/raydium-io/raydium-idl), [orca-so/whirlpools](https://github.com/orca-so/whirlpools), [dlmm-sdk](https://github.com/MeteoraAG/dlmm-sdk), [damm-v1-sdk](https://github.com/MeteoraAG/damm-v1-sdk), [damm-v2](https://github.com/MeteoraAG/damm-v2), [pump-public-docs](https://github.com/pump-fun/pump-public-docs) and [jupiter-cpi](https://github.com/jup-ag/jupiter-cpi).

The handler is [`src/handlers/swaps.ts`](src/handlers/swaps.ts). It stores one entity, `DailyVenueSwaps`, with one row per UTC day and program holding `swaps`, `topLevel` and `inner`.

How it counts.

- A swap is one matched swap instruction, top-level or inner.
- Jupiter routes are kept on their own row and left out of every share. The pool swaps a route triggers are already counted under each DEX, so adding the route as well would count the same trade twice.
- A multi-hop instruction counts once per program it runs in. A PumpSwap multi-hop that also trades on the Pump.fun curve shows up once under each.
- Only successful transactions count, since HyperSync doesn't serve the instructions of failed transactions.
- Days are UTC. The slot at each midnight was found from block times.
- Venues that publish no IDL or swap layout, such as private market makers that only quote through aggregators, and order books such as Phoenix and OpenBook aren't covered.

## Run it

You need Node.js 22.15 or newer, pnpm, Docker for the local Postgres, and a free API token from [envio.dev/app/api-tokens](https://envio.dev/app/api-tokens).

```bash
git clone https://github.com/enviodev/hypersync-use-cases.git
cd hypersync-use-cases/solana/solana-dex-swaps-by-program
cp .env.example .env   # then paste your token into ENVIO_API_TOKEN
pnpm install
pnpm codegen
pnpm dev
```

`config.yaml` covers one UTC day, 9 Nov 2026 (slots 467,108,373 to 467,510,826). A day is about 34M matched instructions and took about 20 minutes on a laptop. For the week above we ran one copy of the indexer per day, side by side, each with its own database. Change `start_slot` and `end_slot` to index another window.

When it finishes, query `DailyVenueSwaps` in the GraphQL playground at http://localhost:8080 (local admin secret `testing`).

```graphql
{
  DailyVenueSwaps(order_by: [{ day: asc }, { swaps: desc }]) { day program swaps topLevel inner }
}
```

### Make it live

To follow Solana in real time instead of one fixed day, set `start_slot: latest` and remove `end_slot` in `config.yaml`.

### Deploy it

Push your fork to GitHub and deploy it on [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service) to get a hosted GraphQL endpoint.

## Check the numbers

- **HyperSync.** On two windows, 100 slots and 2,000 slots (467,300,000 to 467,301,999, run from a clean copy of this folder), the indexer's counts matched a direct HyperSync count of the same instructions exactly, for every program.
- **Solana RPC, as the comparison.** In four single slots spread across the week (464,700,001, 465,900,123, 466,800,777 and 467,400,555) we decoded every successful transaction from Solana RPC [`getBlock`](https://solana.com/docs/rpc/http/getblock), top-level and inner, and counted the same instructions. Every program matched exactly.

## Build your own with an AI agent

Paste this into Claude Code, Cursor or any coding agent from this folder.

```text
This is an Envio HyperIndex indexer for Solana (ecosystem: svm). Read README.md,
config.yaml, schema.graphql and src/handlers/swaps.ts, then the Solana docs at
https://docs.envio.dev/docs/HyperIndex/solana. My API token is in the
ENVIO_API_TOKEN environment variable.

Add a new DEX program to config.yaml and SWAPS in the handler, taking its program
ID and swap instruction discriminators from the project's own IDL or repo, and
list only instructions that trade. Then add an hourly rollup next to
DailyVenueSwaps. Set start_slot and end_slot to a 100-slot window, run
`pnpm codegen` and `pnpm dev`, and check the new program's count against a
direct HyperSync query for the same instructions and slots.
```

## Links

- [Indexing Solana with HyperIndex](https://docs.envio.dev/docs/HyperIndex/solana)
- [Solana instruction handlers](https://docs.envio.dev/docs/HyperIndex/solana/instruction-handlers)
- [Solana configuration file](https://docs.envio.dev/docs/HyperIndex/solana/configuration)
- [HyperSync on Solana](https://docs.envio.dev/docs/HyperSync/solana)
- [Envio Cloud](https://docs.envio.dev/docs/HyperIndex/hosted-service)
- [Envio Discord](https://discord.gg/envio)
